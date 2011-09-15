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
