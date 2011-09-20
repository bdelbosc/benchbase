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
"""Extend sqlite aggregate functions"""
from math import isnan


def to_float(value):
    """Return None if value is not a valid float."""
    try:
        ret = float(value)
        if isnan(ret):
            ret = None
    except ValueError:
        ret = None
    return ret


class Percentile(object):
    def __init__(self, percentile):
        self.percentile = percentile
        self.items = []

    def step(self, value):
        v = to_float(value)
        if v is not None:
            self.items.append(v)

    def finalize(self):
        if len(self.items) < 1:
            return None
        index = int(len(self.items) * self.percentile)
        self.items.sort()
        return self.items[index]


class P10(Percentile):
    def __init__(self):
        Percentile.__init__(self, 0.1)


class Median(Percentile):
    def __init__(self):
        Percentile.__init__(self, 0.5)


class P90(Percentile):
    def __init__(self):
        Percentile.__init__(self, 0.9)


class P95(Percentile):
    def __init__(self):
        Percentile.__init__(self, 0.95)


class P98(Percentile):
    def __init__(self):
        Percentile.__init__(self, 0.98)


class StdDev(object):
    """Sample standard deviation"""
    def __init__(self):
        self.items = []

    def step(self, value):
        v = to_float(value)
        if v is not None:
            self.items.append(v)

    def finalize(self):
        if len(self.items) < 1:
            return None
        items = self.items
        total = sum(items)
        avg = total / len(items)
        print "tot: %f, avg: %f" % (total, avg)
        sdsq = sum([(i - avg) ** 2 for i in items])
        ret = (sdsq / (len(items) - 1 or 1)) ** 0.5
        return ret


class First(object):
    """Sample standard deviation"""
    def __init__(self):
        self.first = None

    def step(self, value):
        if self.first is None and value:
            self.first = value

    def finalize(self):
        return self.first


def interval(start, period, t):
    return start + (int(t - start) / int(period)) * period


def fl_label(step, number, rtype, description):
    """Build a funkload label."""
    if description:
        lb = description
    else:
        lb = rtype
    ret = "%3.3d-%3.3d %s" % (step, number, lb)
    return ret


def add_aggregates(db):
    db.create_aggregate('p10', 1, P10)
    db.create_aggregate('med', 1, Median)
    db.create_aggregate('p90', 1, P90)
    db.create_aggregate('p95', 1, P95)
    db.create_aggregate('p98', 1, P98)
    db.create_aggregate('stddev', 1, P98)
    db.create_aggregate('first', 1, First)
    db.create_function('interval', 3, interval)
    db.create_function('fl_label', 4, fl_label)
