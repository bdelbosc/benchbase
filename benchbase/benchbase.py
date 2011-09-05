#!/usr/bin/env python
# (C) Copyright 2008-2011 Nuxeo SAS <http://nuxeo.com>
# Authors: Benoit Delbosc <ben@nuxeo.com>
# Original idea Roman Mackovcak (recycl)
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
import sqlite3
import xml.etree.cElementTree as etree
import logging
import hashlib
import datetime
from commands import getstatusoutput
from optparse import OptionParser, TitledHelpFormatter
import pkg_resources
from docutils.core import publish_cmdline
from mako.lookup import TemplateLookup


TEMPLATE_LOOKUP = TemplateLookup(
    directories=[pkg_resources.resource_filename('benchbase', '/templates')],
    )

USAGE = """benchbase [--version] [--logfile=LOGFILE] [--database=DATABASE] COMMAND [OPTIONS] [ARGUMENT]

COMMANDS:

  list
     List the imported benchmark in the database.

  info BID
     Give more information about the benchmark with the bid number (benchmark identifier).

  import [--jmeter|--funkload|--comment] FILE
     Import the benchmark result into the database. Output the BID number.

  report --output REPORT_DIR BID
     Generate the report for the imported benchmark

EXAMPLES:

   benchbase list
      List of imported benchmarks.

   benchbase import -m"Tir 42" jmeter-2010.xml
      Import a JMeter benchmark result file.

   benchbase report 12 -o /tmp/report-tir43
      Build the report of benchmark bid 12 into /tmp/report-tir43 directory

"""

SCHEMAS = {
    # bench table
    'bench': {
        'md5sum': 'TEXT',   # md5sum of the file
        'filename': 'TEXT',  # imported filename
        'date': 'TEXT',  # date of import
        'comment': 'TEXT',
        'generator': 'TEXT',  # jmeter or funkload
        },
    # sysstat table
    'host': {
        'bid': 'INTEGER',
        'host': 'TEXT',
        'comment': 'TEXT',
        },
    'cpu': {
        'bid': 'INTEGER',
        'host': 'TEXT',
        'date': 'TEXT',
        'usr': 'REAL',
        'nice': 'REAL',
        'sys': 'REAL',
        'iowait': 'REAL',
        'steal': 'REAL',
        'irq': 'REAL',
        'soft': 'REAL',
        'guest': 'REAL',
        'idle': 'REAL'
        },
    'disk': {
        'bid': 'INTEGER',
        'host': 'TEXT',
        'date': 'TEXT',
        'dev': 'TEST',
        'tps': 'REAL',
        'rd_sec_per_s': 'REAL',
        'wr_sec_per_s': 'REAL',
        'util': 'REAL'
        },

    # jmeter table
    'testresults': {
        'bid': 'INTEGER',
        'version': 'TEXT'
        },
    # jmeter table
    'sample': {
        # additional fields
        'bid': 'INTEGER',
        'stamp': 'INTEGER',    # timestamp in second
        'success': 'INTEGER',  # cast on s field
        # jmeter fields
        'by': 'INTEGER',   # Bytes
        'de': 'TEXT',      # Data encoding
        'dt': 'TEXT',      # Data type
        'ec': 'INTEGER',   # Error count (0 or 1, unless multiple samples are aggregated)
        'hn': 'TEXT',      # Hostname where the sample was generated
        'it': 'INTEGER',   # Idle Time = time not spent sampling (milliseconds) (generally 0)
        'lb': 'TEXT',      # Label
        'lt': 'INTEGER',   # Latency = time to initial response (milliseconds) - not all samplers support this
        'na': 'INTEGER',   # Number of active threads for all thread groups
        'ng': 'INTEGER',   # Number of active threads in this group
        'rc': 'INTEGER',   # Response Code (e.g. 200)
        'rm': 'TEXT',      # Response Message (e.g. OK)
        's': 'TEXT',       # Success flag (true/false)
        'sc': 'INTEGER',   # Sample count (1, unless multiple samples are aggregated)
        't': 'INTEGER',    # Elapsed time (milliseconds)
        'tn': 'TEXT',      # Thread Name
        'ts': 'INTEGER',   # timeStamp (milliseconds since midnight Jan 1, 1970 UTC)
        'varname': 'TEXT'  # Value of the named variable (versions of JMeter after 2.3.1)
        },
}

CREATE_QUERY = 'CREATE TABLE IF NOT EXISTS [{table}]({fields})'
INSERT_QUERY = 'INSERT INTO {table} ({columns}) VALUES ({values})'
LOG_FILENAME = 'btracker.log'

DEFAULT_LOG = "~/benchbase.log"
DEFAULT_DB = "~/benchbase.db"


def get_version():
    """Retrun the FunkLoad package version."""
    return pkg_resources.get_distribution('benchbase').version


def render_template(template_name, **kwargs):
    mytemplate = TEMPLATE_LOOKUP.get_template(template_name)
    return mytemplate.render(**kwargs)


def md5sum(filename):
    f = open(filename)
    md5 = hashlib.md5()
    while True:
        data = f.read(8192)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()


def gnuplot(script_path):
    """Execute a gnuplot script."""
    path = os.path.dirname(os.path.abspath(script_path))
    if sys.platform.lower().startswith('win'):
        # commands module doesn't work on win and gnuplot is named
        # wgnuplot
        ret = os.system('cd "' + path + '" && wgnuplot "' +
                        os.path.abspath(script_path) + '"')
        if ret != 0:
            raise RuntimeError("Failed to run wgnuplot cmd on " +
                               os.path.abspath(script_path))

    else:
        cmd = 'cd ' + path + '; gnuplot ' + os.path.abspath(script_path)
        ret, output = getstatusoutput(cmd)
        if ret != 0:
            raise RuntimeError("Failed to run gnuplot cmd: " + cmd +
                               "\n" + str(output))


def generateHtml(rst_file, html_file, report_dir):
    """Ask docutils to convert our rst file into html."""
    css_content = pkg_resources.resource_string('benchbase', '/templates/benchbase.css')
    css_dest_path = os.path.join(report_dir, 'benchbase.css')
    f = open(css_dest_path, 'w')
    f.write(css_content)
    f.close()
    cmdline = "-t --stylesheet-path=%s %s %s" % ('benchbase.css',
                                                 os.path.basename(rst_file),
                                                 os.path.basename(html_file))
    cmd_argv = cmdline.split(' ')
    pwd = os.getcwd()
    os.chdir(report_dir)
    publish_cmdline(writer_name='html', argv=cmd_argv)
    os.chdir(pwd)


def initializeDb(options):
    if options.rmdatabase and os.path.exists(options.database):
        logging.warning("Erasing database: " + options.database)
        os.unlink(options.database)
    db = sqlite3.connect(options.database)
    table_names = SCHEMAS.keys()
    for table_name in table_names:
        sql_create = CREATE_QUERY.format(
            table=table_name,
            fields=", ".join(['{0} {1}'.format(name, type) for name, type in SCHEMAS[table_name].items()]))
        logging.debug('Creating table {0}'.format(table_name))
        try:
            logging.debug(sql_create)
            db.execute(sql_create)
        except Exception, e:
            logging.warning(e)
    db.commit()
    return db


def listBenchmarks(db):
    c = db.cursor()
    c.execute('SELECT ROWID, date, generator, filename, comment FROM bench')
    print "%5s %-19s %-8s %-30s %s" % ('bid', 'Imported', 'Tool', 'Filename', 'Comment')
    for row in c:
        print "%5d %19s %-8s %-30s %s" % (row[0], row[1][:19], row[2], os.path.basename(row[3]), row[4])
    c.close()


class Sar(object):
    """Handle sysstat sar file."""
    def __init__(self, db, options):
        self.options = options
        self.db = db
        self.table_names = SCHEMAS.keys()

    def doImport(self, bid, filename):
        c = self.db.cursor()
        options = self.options
        host = options.host
        t = (bid, host, options.comment)
        c.execute('INSERT INTO host (bid, host, comment) VALUES (?, ?, ?)', t)
        f = open(filename)
        in_cpu = False
        in_disk = False
        while True:
            line = f.readline()
            if not line:
                break
            if 'CPU      %usr' in line:
                in_cpu = True
                continue
            if 'DEV       tps' in line:
                in_disk = True
                continue
            if in_cpu:
                if not 'all' in line:
                    continue
                if 'Average' in line:
                    in_cpu = False
                    continue
                t = [bid, host] + line.split()
                t.remove('all')
                c.execute('INSERT INTO cpu (bid, host, date, usr, nice, sys, iowait, steal, irq, soft, '
                          'guest, idle) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', t)
            elif in_disk:
                if 'Average' in line:
                    in_disk = False
                    break
                r = line.split()
                t = [bid, host, r[0], r[1], r[2], r[3], r[4], r[9]]
                c.execute('INSERT INTO disk (bid, host, date, dev, tps, rd_sec_per_s, wr_sec_per_s, util)'
                          ' VALUES (?, ?, ?, ?, ?, ?, ?, ?)', t)
        c.close()
        self.db.commit()


class Jmeter(object):
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

    def doImport(self, filename):
        md5 = md5sum(filename)
        if self.alreadyImported(md5, filename):
            return
        bid = self.registerBench(md5, filename)
        db = self.db
        logging.info("Importing JMeter file: {0} into bid: {1}".format(filename, bid))
        with open(filename) as xml_file:
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
                    print ".",
                except Exception, e:
                    logging.warning(e)
                    print "x",
                finally:
                    row.clear()
            print "\n"
            db.commit()
            del(tree)
        # finalize
        db.execute("UPDATE sample SET stamp = ts/1000;")
        db.execute("UPDATE sample SET success = 1 WHERE s IN ('true', 'TRUE', 'True');")
        db.execute("UPDATE sample SET success = 0 WHERE s NOT IN ('true', 'TRUE', 'True');")
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

    def buildReport(self, bid):
        output_dir = self.options.output
        if not os.access(output_dir, os.W_OK):
            os.mkdir(output_dir, 0775)
        info = self.getInfo(bid)
        params = {'dbpath': self.options.database,
                  'output_dir': output_dir,
                  'start': info['start'][11:19],
                  'end': info['end'],
                  'bid': bid}
        samples = info['samples'].keys() + ['global', ]
        for sample in samples:
            params['sample'] = sample
            params['filter'] = " AND lb = '%s' " % sample
            params['title'] = "Sample: " + sample
            if sample == 'global':
                params['filter'] = ''
                params['title'] = "Global"
            script = render_template('gnuplot.mako', **params)
            script_path = os.path.join(output_dir, sample + ".gplot")
            f = open(script_path, 'w')
            f.write(script)
            f.close()
            gnuplot(script_path)
        report = render_template('report.mako', **info)
        rst_path = os.path.join(output_dir, "index.rst")
        f = open(rst_path, 'w')
        f.write(report)
        f.close()
        html_path = os.path.join(output_dir, "index.html")
        generateHtml(rst_path, html_path, output_dir)
        logging.info('Report generated: ' + html_path)


def initLogging(options):
    level = logging.INFO
    if options.verbose:
        level = logging.DEBUG
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename=options.logfile,
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(level)
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def main():
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

    options, args = parser.parse_args(sys.argv)
    initLogging(options)
    if len(args) == 1:
        parser.error("Missing options")
    if args[1].lower() in ('l', 'li', 'list'):
        db = initializeDb(options)
        listBenchmarks(db)
        db.close()
    if args[1].lower() in ('imp', 'import'):
        if len(args) != 3:
            parser.error("Missing import file")
            return
        if options.funkload:
            raise NotImplementedError("Sorry, FunkLoad import is not yet available.")
        if options.jmeter:
            db = initializeDb(options)
            jm = Jmeter(db, options)
            bid = jm.doImport(args[2])
            if bid:
                print "File imported, bench identifier (bid): %d" % bid
            db.close()
    if args[1].lower() in ('info', ):
        if len(args) != 3:
            parser.error('Missing bid')
            return
        db = initializeDb(options)
        jm = Jmeter(db, options)
        print """bid: %(bid)s, from %(start)s to %(end)s, samples: %(count)d, errors: %(error)d""" % jm.getInfo(args[2])
        db.close()
    if args[1].lower() in ('report', ):
        if len(args) != 3:
            parser.error('Missing bid')
            return
        if not options.output:
            parser.error('Missing --output option')
            return
        db = initializeDb(options)
        jm = Jmeter(db, options)
        jm.buildReport(args[2])
        db.close()
    if args[1].lower() in ('add', 'addsar'):
        if len(args) != 4:
            parser.error('Expecting BID and FILE argument')
            return
        if not options.host:
            parser.error('Missing --host option')
            return
        db = initializeDb(options)
        sar = Sar(db, options)
        sar.doImport(args[2], args[3])
        db.close()


if __name__ == '__main__':
    main()
