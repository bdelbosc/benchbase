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
import os
from tempfile import mkdtemp
from unittest import TestCase
from benchbase.main import main
import benchbase.sqliteaggregate as aggregate


class FunctionalTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls._test_dir = mkdtemp('_benchbase')
        cls._db = os.path.join(cls._test_dir, 'bb.db')
        cls._log = os.path.join(cls._test_dir, 'bb.log')

    @classmethod
    def tearDownClass(cls):
        pass

    def opts(self):
        return  " -d %s -l %s" % (self._db, self._log)

    def bb(self, cmd):
        return main(('bb ' + cmd + self.opts()).split())

    def test_00_list(self):
        ret = self.bb('list')
        self.assertEquals(0, ret)

    def test_01_import_jmeter(self):
        ret = self.bb('import tests/bench1/jmeter.xml.gz -m bench_comment')
        self.assertEquals(0, ret)

    def test_02_list(self):
        ret = self.bb('list')
        self.assertEquals(0, ret)

    def test_03_info(self):
        ret = self.bb('info 1')
        self.assertEquals(0, ret)

    def test_04_import_jmeter_fail(self):
        # check that we can not import twice the same file
        ret = self.bb('import tests/bench1/jmeter.xml.gz -m bench_comment')
        self.assertNotEquals(0, ret)

    def test_10_import_sar(self):
        ret = self.bb('addsar 1 tests/bench1/sar.log.gz -H server_name')
        self.assertEquals(0, ret)

    def test_11_info(self):
        ret = self.bb('info 1')
        self.assertEquals(0, ret)

    def test_20_report(self):
        ret = self.bb('report -o %s 1' %
                      os.path.join(self._test_dir, 'report1'))
        self.assertEquals(0, ret)

    def test_50_import_funkload(self):
        ret = self.bb('import tests/bench-10-fl/funkload.xml.gz -f -m fl_bench_comment')
        self.assertEquals(0, ret)


class AggregateTestCase(TestCase):

    def test_percentile_null(self):
        p = aggregate.P10()
        p.step(float('nan'))
        p.step('null')
        self.assertEquals(None, p.finalize())

    def test_percentile(self):
        p10 = aggregate.P10()
        med = aggregate.Median()
        p90 = aggregate.P90()
        p95 = aggregate.P95()
        p98 = aggregate.P98()
        for i in range(99, 0, -1):
            p10.step(i)
            med.step(i)
            p90.step(i)
            p95.step(i)
            p98.step(i)

        v10 = p10.finalize()
        vmed = med.finalize()
        v90 = p90.finalize()
        v95 = p95.finalize()
        v98 = p98.finalize()

        self.assertEquals(v10, 10)
        self.assertEquals(vmed, 50)
        self.assertEquals(v90, 90)
        self.assertEquals(v95, 95)
        self.assertEquals(v98, 98)

    def test_stddev_const(self):
        sd = aggregate.StdDev()
        for i in range(100):
            sd.step(50)
        ret = sd.finalize()
        self.assertEquals(ret, 0)

    def test_stddev_set(self):
        sd = aggregate.StdDev()
        for i in [2, 4, 4, 4, 5, 5, 7, 9]:
            sd.step(i)
        ret = sd.finalize()
        self.assertEquals(ret, (32 / 7.) ** .5)


class IntervalTestCase(TestCase):

    def test_interval(self):
        interval = aggregate.interval
        self.assertEquals(100, interval(100, 10, 100))
        self.assertEquals(100, interval(100, 10, 109))
        self.assertEquals(110, interval(100, 10, 110))
        self.assertEquals(110, interval(100, 10, 111))
        self.assertEquals(110, interval(100, 10, 119))

        self.assertEquals(91, interval(101, 10, 100))
        self.assertEquals(101, interval(101, 10, 109))
        self.assertEquals(101, interval(101, 10, 110))
        self.assertEquals(111, interval(101, 10, 111))
        self.assertEquals(111, interval(101, 10, 119))
