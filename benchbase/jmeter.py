#!/usr/bin/env python
# -*- coding: utf_8 -*
# (C) Copyright 2008-2011 Nuxeo SAS <http://nuxeo.com>
# Authors: Benoit Delbosc <ben@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
"""Extract information from an JMeter result file."""
import os
import xml.etree.cElementTree as etree
import logging
import datetime
import csv
from model import INSERT_QUERY, SCHEMAS
from util import md5sum, mygzip

# 1312804821705,647,label,scenar,text,true,347447,1,2,536
JTL_COLUMN = ['ts', 't', 'lb', 'tn', 'de', 's', 'by', 'ng', 'na', 'lt']


class JMeter(object):
    """JMeter importer / renderer"""
    def __init__(self, db, options):
        self.options = options
        self.db = db
        self.table_names = SCHEMAS.keys()

    def alreadyImported(self, md5, filename):
        t = (md5,)
        c = self.db.cursor()
        c.execute("SELECT ROWID, date FROM bench WHERE md5sum = ? ", t)
        row = c.fetchone()
        c.close()
        if row:
            logging.info("%s already imported with bid: %d at %s" % (filename, row[0], row[1][:19]))
            return True
        return False

    def registerBench(self, md5, filename):
        c = self.db.cursor()
        t = (md5, filename, datetime.datetime.now(), self.options.comment, 'JMeter')
        c.execute("INSERT INTO bench (md5sum, filename, date, comment, generator) VALUES (?, ?, ?, ?, ?)", t)
        t = (md5, )
        c.execute("SELECT rowid FROM bench WHERE md5sum = ? ", t)
        self.bid = c.fetchone()[0]
        c.close()
        return self.bid

    def importXmlFile(self, bid, filename):
        db = self.db
        if filename.endswith('.gz'):
            f = mygzip(filename)
        else:
            f = open(filename)
        count = 0
        error = 0
        with f as xml_file:
            tree = etree.iterparse(xml_file)
            for events, row in tree:
                table_name = row.tag.lower()
                if table_name not in self.table_names:
                    continue
                try:
                    logging.debug(row.attrib.keys())
                    cols = 'bid' + ', ' + ', '.join(row.attrib.keys())
                    values = ('?, ' * (len(row.attrib.keys()) + 1))[:-2]
                    data = row.attrib.values()
                    data.insert(0, bid)
                    db.execute(INSERT_QUERY.format(
                            table=table_name,
                            columns=cols,
                            values=values), data)
                    count += 1
                except Exception, e:
                    logging.warning(e)
                    error += 1
                finally:
                    row.clear()
            db.commit()
            del(tree)
            logging.info('%i samples imported, %i error(s).' % (count, error))

    def importJtlFile(self, bid, filename):
        db = self.db
        if filename.endswith('.gz'):
            f = mygzip(filename)
        else:
            f = open(filename)
        jtlReader = csv.reader(f)
        values = ('?, ' * (len(JTL_COLUMN) + 1))[:-2]
        insert_query = 'INSERT INTO sample (bid, ' + ', '.join(JTL_COLUMN) + ') VALUES (' + values + ')'
        print insert_query
        count = 0
        error = 0
        for row in jtlReader:
            row = [unicode(cell, 'utf-8').encode('ascii', 'ignore') for cell in row]
            try:
                db.execute(insert_query, [bid, ] + row)
                count += 1
            except Exception, e:
                logging.warning(e)
                error += 1
                print "x",
        db.commit()
        logging.info('%i samples imported, %i error(s).' % (count, error))

    def doImport(self, filename):
        md5 = md5sum(filename)
        if self.alreadyImported(md5, filename):
            return
        bid = self.registerBench(md5, filename)
        db = self.db
        logging.info("Importing JMeter file: {0} into bid: {1}".format(filename, bid))
        if filename.endswith('xml') or filename.endswith('xml.gz'):
            self.importXmlFile(bid, filename)
        else:
            self.importJtlFile(bid, filename)
        # finalize
        db.execute("UPDATE sample SET stamp = ts/1000 WHERE stamp IS NULL;")
        db.execute("UPDATE sample SET success = 1 WHERE s IN ('true', 'TRUE', 'True') AND success IS NULL;")
        db.execute("UPDATE sample SET success = 0 WHERE s NOT IN ('true', 'TRUE', 'True') AND success IS NULL;")
        db.commit()
        return bid

    def getInfo(self, bid):
        t = (bid, )
        c = self.db.cursor()
        c.execute("SELECT date, comment, generator, filename FROM bench WHERE ROWID = ?", t)
        try:
            imported, comment, generator, filename = c.fetchone()
        except TypeError:
            logging.error('Invalid bid: %s' % bid)
            raise ValueError('Invalid bid: %s' % bid)
        c.execute("SELECT COUNT(stamp), datetime(MIN(stamp), 'unixepoch', 'localtime')"
                  ", time(MAX(stamp), 'unixepoch', 'localtime') FROM sample WHERE bid = ?", t)
        count, start, end = c.fetchone()
        c.execute("SELECT COUNT(stamp) FROM sample WHERE bid = ? AND success = 0", t)
        error = c.fetchone()[0]
        c.execute("SELECT DISTINCT(lb) FROM sample WHERE bid = ?", t)
        sampleNames = [row[0] for row in c]
        c.execute("SELECT MAX(na), MAX(stamp) - MIN(stamp), AVG(t), MAX(t), MIN(t) FROM sample WHERE bid = ?", t)
        maxThread, duration, avgt, maxt, mint = c.fetchone()
        samples = {}
        for sample in sampleNames:
            t = (bid, sample)
            c.execute("SELECT AVG(t), MAX(t), MIN(t), COUNT(t) FROM sample WHERE bid = ? AND lb = ?", t)
            row = c.fetchone()
            samples[sample] = {'avgt': row[0] / 1000., 'maxt': row[1] / 1000., 'mint': row[2] / 1000.,
                               'count': row[3], 'duration': duration}
            c.execute("SELECT COUNT(t) FROM sample WHERE bid = ? AND lb = ? AND success = 0", t)
            samples[sample]['error'] = c.fetchone()[0]
        return {'bid': bid, 'count': count, 'start': start, 'end': end, 'filename': os.path.basename(filename),
                'error': error, 'samples': samples, 'imported': imported[:19], 'comment': comment,
                'maxThread': maxThread, 'duration': duration, 'avgt': avgt / 1000.,
                'maxt': maxt / 1000., 'mint': mint / 1000., 'generator': generator}
