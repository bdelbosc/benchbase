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
"""Extract information from an FunkLoad result file."""
import os
import xml.etree.cElementTree as etree
import logging
import datetime
from model import INSERT_QUERY, SCHEMAS
from util import md5sum, mygzip, truncate, str2id


class Bencher(object):
    """Base class for FunkLoad or JMeter importer / renderer"""
    _name = None
    _prefix = None
    _table = None
    _label = None
    _cvus = None

    def __init__(self, db, options):
        self.options = options
        self.db = db
        self.table_names = SCHEMAS.keys()

    @staticmethod
    def getBencherForBid(db, options, bid):
        c = db.cursor()
        t = (bid, )
        c.execute("SELECT generator, filename FROM bench WHERE ROWID = ?", t)
        generator = c.fetchone()[0]
        c.close()
        if generator.lower() == 'funkload':
            from funkload import FunkLoad
            return FunkLoad(db, options)
        elif generator.lower() == 'jmeter':
            from jmeter import JMeter
            return JMeter(db, options)
        raise ValueError('Invalid bid type')

    def alreadyImported(self, md5, filename):
        t = (md5, )
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
        t = (md5, filename, datetime.datetime.now(), self.options.comment,
             self._name)
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
                tag_name = row.tag.lower()
                if tag_name == 'httpsample':
                    tag_name = 'sample'
                table_name = self._prefix + tag_name
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

    def importOtherFormat(self, bid, filename):
        logging.error('Expecting an .xml or .xml.gz file')
        raise ValueError('Bad filename ' + filename)

    def doImport(self, filename):
        md5 = md5sum(filename)
        if self.alreadyImported(md5, filename):
            return
        bid = self.registerBench(md5, filename)
        db = self.db
        logging.info("Importing {0}: {1} into bid: {2}".format(self._name,
                                                               filename, bid))
        if filename.endswith('xml') or filename.endswith('xml.gz') or filename.endswith('jtl') or filename.endswith('jtl.gz'):
            self.importXmlFile(bid, filename)
        else:
            self.importOtherFormat(bid, filename)
        self.finalizeImport(bid, db)
        db.commit()
        return bid

    def finalizeImport(self, bid, db):
        pass

    def _get_interval_info(self):
        return "SELECT time(interval(?, ?, stamp), 'unixepoch', 'localtime'), COUNT(t), AVG(t)/1000, MAX(t)/1000., MIN(t)/1000.,  STDDEV(t)/1000,  "\
            " MED(t)/1000, P10(t)/1000, P90(t)/1000, P95(t)/1000, P98(t)/1000, TOTAL(t)/1000, TOTAL(success), "\
            " AVG(na) FROM j_sample WHERE bid = ?"

    def getIntervalInfo(self, bid, start, period, sample, c=None):
        close_cursor = False
        if c is None:
            c = self.db.cursor()
            close_cursor = True
        ret = [['time', 'count', 'avg', 'max', 'min', 'stdev', 'med', 'p10', 'p90', 'p95', 'p98', 'total', 'success', 'threads', 'tput', 'error_rate']]
        t = [start, period, bid]
        query = self._get_interval_info()
        if sample.lower() != 'all':
            t.append(sample)
            query += " AND lb = ?"
        t = t + [start, period]
        query = query + " GROUP BY interval(?, ?, stamp)"
        logging.debug("query: %s, var: %s" % (query, str(t)))
        c.execute(query, t)
        for row in c:
            error_rate = (row[1] - row[12]) * 100. / row[1]
            ret.append(row + (row[1] / float(period), error_rate))
        if close_cursor:
            c.close()
        return ret

    def _get_period_info_query(self):
        return "SELECT COUNT(t), AVG(t), MAX(t), MIN(t),  STDDEV(t),  MED(t), "\
            "P10(t), P90(t), P95(t), P98(t), TOTAL(t), TOTAL(success) "\
            "FROM {table} WHERE bid = ? AND stamp >= ? AND stamp < ?"

    def getPeriodInfo(self, bid, start, period, sample, c=None, total=None):
        close_cursor = False
        if c is None:
            c = self.db.cursor()
            close_cursor = True
        query = self._get_period_info_query()
        t = [bid, start, start + period]
        if sample.lower() != 'all':
            t.append(sample)
            query += " AND lb = ?"
        # print "query: %s, var: %s" % (query, str(t))
        logging.debug(query + str(t))
        c.execute(query, t)
        row = c.fetchone()
        ret = {'name': sample, 'count': row[0],
               'avgt': row[1], 'maxt': row[2], 'mint': row[3],
               'stddevt': row[4], 'medt': row[5], 'p10t': row[6],
               'p90t': row[7], 'p95t': row[8], 'p98t': row[9],
               'total': row[10], 'success': row[11],
               'tput': row[0] / float(period),
               'filename': str2id(sample),
               'title': sample | truncate(20)}
        ret['error'] = int(ret['count'] - ret['success'])
        ret['success_rate'] = 100.
        if ret['count'] > 0:
            ret['success_rate'] = (100. * ret['success']) / ret['count']
        if total is None or not total:
            ret['percent'] = 100.
        else:
            ret['percent'] = ret['total'] * 100. / total
        if close_cursor:
            c.close()
        return ret

    def _get_info_query(self):
        return "SELECT COUNT(stamp),MIN(stamp), datetime(MIN(stamp), 'unixepoch', 'localtime')" \
            ", time(MAX(stamp), 'unixepoch', 'localtime'), MAX({cvus}), MAX(stamp) - MIN(stamp) "\
            "FROM {table} WHERE bid = ?".format(cvus=self._cvus, table=self._table)

    def _get_extra_info(self, bid, c=None):
        return ""

    def getInfo(self, bid):
        t = (bid, )
        c = self.db.cursor()
        c.execute("SELECT date, comment, generator, filename FROM bench WHERE ROWID = ?", t)
        try:
            imported, comment, generator, filename = c.fetchone()
        except TypeError:
            logging.error('Invalid bid: %s' % bid)
            raise ValueError('Invalid bid: %s' % bid)
        query = self._get_info_query()
        logging.debug(query + str(t))
        c.execute(query, t)
        count, start_stamp, start, end, max_thread, duration = c.fetchone()
        # take in account the samples done in the last second
        duration += 1
        c.execute("SELECT DISTINCT(lb) FROM {table} WHERE bid = ?".format(table=self._table), t)
        sampleNames = [row[0] for row in c]
        all_samples = self.getPeriodInfo(bid, start_stamp, duration, 'all', c)
        all_samples['percent'] = 100
        total = all_samples['total']
        samples = []
        for name in sampleNames:
            samples.append(self.getPeriodInfo(bid, start_stamp, duration, name, c, total))
        samples.sort(cmp=lambda x, y: cmp(x['total'], y['total']), reverse=True)
        extra = self._get_extra_info(bid, c)
        c.close()
        return {'bid': bid, 'count': count, 'start': start, 'end': end, 'filename': os.path.basename(filename),
                'start_stamp': start_stamp, 'imported': imported[:19], 'comment': comment,
                'max_thread': max_thread, 'duration': duration, 'generator': generator,
                'samples': samples, 'all_samples': all_samples, 'error': all_samples['error'],
                'extra': extra}
