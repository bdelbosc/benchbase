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
import xml.etree.cElementTree as etree
import logging
import datetime
from model import INSERT_QUERY, SCHEMAS
from util import md5sum, mygzip


class Bencher(object):
    """Base class for FunkLoad or JMeter importer / renderer"""

    def __init__(self, db, options):
        self.options = options
        self.db = db
        self.table_names = SCHEMAS.keys()

    def _get_name(self):
        raise NotImplemented()

    def _get_prefix(self):
        raise NotImplemented()

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
             self._get_name())
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
                table_name = self._get_prefix() + row.tag.lower()
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

    def doImport(self, filename):
        md5 = md5sum(filename)
        if self.alreadyImported(md5, filename):
            return
        bid = self.registerBench(md5, filename)
        db = self.db
        print "%s %s" % (self.options.funkload, self._get_name())
        logging.info("Importing {0}: {1} into bid: {2}".format(self._get_name(),
                                                               filename, bid))
        if filename.endswith('xml') or filename.endswith('xml.gz'):
            self.importXmlFile(bid, filename)
        else:
            logging.error('Expecting an .xml or .xml.gz file')
            raise ValueError('Bad filename ' + filename)
            return None
        self.finalizeImport(bid, db)
        db.commit()
        return bid

    def finalizeImport(self, bid, db):
        pass
