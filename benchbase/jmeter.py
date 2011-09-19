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
import logging
import csv
from util import mygzip, truncate, str2id
from bencher import Bencher

# 1312804821705,647,label,scenar,text,true,347447,1,2,536
JTL_COLUMN = ['ts', 't', 'lb', 'tn', 'de', 's', 'by', 'ng', 'na', 'lt']


class JMeter(Bencher):
    """JMeter importer / renderer"""

    def __init__(self, db, options):
        Bencher.__init__(self, db, options)

    def _get_name(self):
        return "JMeter"

    def _get_prefix(self):
        return "j_"

    def importJtlFile(self, bid, filename):
        db = self.db
        if filename.endswith('.gz'):
            f = mygzip(filename)
        else:
            f = open(filename)
        jtlReader = csv.reader(f)
        values = ('?, ' * (len(JTL_COLUMN) + 1))[:-2]
        insert_query = 'INSERT INTO j_sample (bid, ' + ', '.join(JTL_COLUMN) + ') VALUES (' + values + ')'
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

    def finalizeImport(self, bid, db):
        db.execute("UPDATE j_sample SET stamp = ts/1000 WHERE stamp IS NULL;")
        db.execute("UPDATE j_sample SET success = 1 WHERE s IN ('true', 'TRUE', 'True') AND success IS NULL;")
        db.execute("UPDATE j_sample SET success = 0 WHERE s NOT IN ('true', 'TRUE', 'True') AND success IS NULL;")

    def getIntervalInfo(self, bid, start, period, sample, c=None):
        close_cursor = False
        if c is None:
            c = self.db.cursor()
            close_cursor = True
        ret = [['time', 'count', 'avg', 'max', 'min', 'stdev', 'med', 'p10', 'p90', 'p95', 'p98', 'total', 'success', 'threads', 'tput', 'error_rate']]
        query = "SELECT time(interval(?, ?, stamp), 'unixepoch', 'localtime'), COUNT(t), AVG(t)/1000, MAX(t)/1000., MIN(t)/1000.,  STDDEV(t)/1000,  "\
            " MED(t)/1000, P10(t)/1000, P90(t)/1000, P95(t)/1000, P98(t)/1000, TOTAL(t)/1000, TOTAL(success), "\
            " AVG(na) FROM j_sample WHERE bid = ?"
        t = [start, period, bid]
        if sample.lower() != 'all':
            t.append(sample)
            query += " AND lb = ?"
        t = t + [start, period]
        query += " GROUP BY interval(?, ?, stamp)"
        logging.debug("query: %s, var: %s" % (query, str(t)))
        c.execute(query, t)
        for row in c:
            error_rate = (row[1] - row[12]) * 100. / row[1]
            ret.append(row + (row[1] / float(period), error_rate))
        if close_cursor:
            c.close()
        return ret

    def getPeriodInfo(self, bid, start, period, sample, c=None):
        close_cursor = False
        if c is None:
            c = self.db.cursor()
            close_cursor = True
        query = "SELECT COUNT(t), AVG(t), MAX(t), MIN(t),  STDDEV(t),  MED(t), P10(t), P90(t), P95(t), P98(t), TOTAL(t), TOTAL(success) "\
            "FROM j_sample WHERE bid = ? AND stamp >= ? AND stamp < ?"
        t = [bid, start, start + period]
        if sample.lower() != 'all':
            t.append(sample)
            query += " AND lb = ?"
        # print "query: %s, var: %s" % (query, str(t))
        logging.debug(query + str(t))
        c.execute(query, t)
        row = c.fetchone()
        ret = {'name': sample, 'count': row[0],
               'avgt': row[1] / 1000., 'maxt': row[2] / 1000., 'mint': row[3] / 1000.,
               'stddevt': row[4] / 1000., 'medt': row[5] / 1000., 'p10t': row[6] / 1000.,
               'p90t': row[7] / 1000., 'p95t': row[8] / 1000., 'p98t': row[9] / 1000.,
               'total': row[10] / 1000., 'success': row[11],
               'tput': row[0] / float(period),
               'filename': str2id(sample),
               'title': sample | truncate(20)}
        ret['error'] = int(ret['count'] - ret['success'])
        ret['success_rate'] = 100.
        if ret['count'] > 0:
            ret['success_rate'] = (100. * ret['success']) / ret['count']
        if close_cursor:
            c.close()
        return ret

    def getInfo(self, bid):
        t = (bid, )
        c = self.db.cursor()
        c.execute("SELECT date, comment, generator, filename FROM bench WHERE ROWID = ?", t)
        try:
            imported, comment, generator, filename = c.fetchone()
        except TypeError:
            logging.error('Invalid bid: %s' % bid)
            raise ValueError('Invalid bid: %s' % bid)
        c.execute("SELECT COUNT(stamp), MIN(stamp), datetime(MIN(stamp), 'unixepoch', 'localtime')"
                  ", time(MAX(stamp), 'unixepoch', 'localtime'), MAX(na), MAX(stamp) - MIN(stamp) FROM j_sample WHERE bid = ?", t)
        count, start_stamp, start, end, max_thread, duration = c.fetchone()
        # take in account the samples done in the last second
        duration += 1
        c.execute("SELECT DISTINCT(lb) FROM j_sample WHERE bid = ?", t)
        sampleNames = [row[0] for row in c]
        all_samples = self.getPeriodInfo(bid, start_stamp, duration, 'all', c)
        samples = []
        for name in sampleNames:
            samples.append(self.getPeriodInfo(bid, start_stamp, duration, name, c))
        samples.sort(cmp=lambda x, y: cmp(x['total'], y['total']), reverse=True)
        return {'bid': bid, 'count': count, 'start': start, 'end': end, 'filename': os.path.basename(filename),
                'start_stamp': start_stamp, 'imported': imported[:19], 'comment': comment,
                'max_thread': max_thread, 'duration': duration, 'generator': generator,
                'samples': samples, 'all_samples': all_samples, 'error': all_samples['error']}
