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
"""
Try to do something usefull with a jmeter output.
"""
import os
import sys
from optparse import OptionParser, TitledHelpFormatter
from util import get_version, init_logging
from command import *

DEFAULT_DB = "~/benchbase.db"
DEFAULT_LOG = "~/benchbase.log"

USAGE = """benchbase [--version] [--logfile=LOGFILE] [--database=DATABASE] COMMAND [OPTIONS] [ARGUMENT]

COMMANDS:

  list
     List the imported benchmark in the database.

  info BID
     Give more information about the benchmark with the bid number (benchmark identifier).

  import [--jmeter|--funkload|--comment] FILE
     Import the benchmark result into the database. Output the BID number.

  addsar --host HOST [--comment COMMENT] BID SAR
     Import the text sysstat sar output

  report --output REPORT_DIR BID
     Generate the report for the imported benchmark

EXAMPLES

   benchbase list
      List of imported benchmarks.

   benchbase import -m"Run 42" jmeter-2010.xml
      Import a JMeter benchmark result file, this will output a BID number.
.
   benchbase addsar -H"localhost" -m"bencher host" 1 /tmp/sysstat-sar.log.gz
      Attach a gzipped sysstat sar file for the bench BID 1.

   benchbase report 1 -o /tmp/report-run42
      Build the report of benchmark BID 1 into /tmp/report-run42 directory.

"""


def main(argv=sys.argv):
    """Main test"""
    global USAGE
    parser = OptionParser(USAGE, formatter=TitledHelpFormatter(),
                          version="benchbase %s" % get_version())
    parser.add_option("-v", "--verbose", action="store_true",
                      help="Verbose output")
    parser.add_option("-l", "--logfile", type="string",
                      default=os.path.expanduser(DEFAULT_LOG),
                      help="Log file path")
    parser.add_option("-d", "--database", type="string",
                      default=os.path.expanduser(DEFAULT_DB),
                      help="SQLite db path")
    parser.add_option("-m", "--comment", type="string",
                      help="Add a comment")
    parser.add_option("-j", "--jmeter", action="store_true",
                      default=True,
                      help="JMeter input file")
    parser.add_option("-f", "--funkload", action="store_true",
                      default=False,
                      help="FunkLoad input file")
    parser.add_option("--rmdatabase", action="store_true",
                      default=False,
                      help="Remove existing database")
    parser.add_option("-o", "--output", type="string",
                      help="Report output directory")
    parser.add_option("-H", "--host", type="string",
                      help="Host name when adding sar report")
    parser.add_option("-r", "--runningavg", type="int",
                      default=5,
                      help="Number of second to compute the running average.")
    parser.add_option("--chart-width", type="int",
                      default=800,
                      help="Width of charts in report.")
    parser.add_option("--chart-height", type="int",
                      default=768,
                      help="Heigth of charts in report.")
    parser.add_option("--period", type="int",
                      help="Resolution in second")

    options, args = parser.parse_args(argv)
    init_logging(options)
    if len(args) == 1:
        parser.error("Missing command")
    cmd = args[1]
    fn = globals()['cmd_' + cmd]
    ret = fn(args[2:], options)
    return ret


if __name__ == '__main__':
    ret = main()
    sys.exit(ret)
