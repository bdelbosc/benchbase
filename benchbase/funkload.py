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
import logging
from bencher import Bencher


class FunkLoad(Bencher):
    """FunkLoad importer / renderer"""

    def __init__(self, db, options):
        Bencher.__init__(self, db, options)

    def _get_name(self):
        return "FunkLoad"

    def _get_prefix(self):
        return "f_"

    def finalizeImport(self, bid, db):
        db.execute("UPDATE f_response SET stamp = time WHERE stamp IS NULL;")
        db.execute("UPDATE f_response SET success = 1 WHERE result = 'Successful' AND success IS NULL;")
        db.execute("UPDATE f_response SET success = 0 WHERE success IS NULL")
