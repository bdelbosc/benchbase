#!/bin/env python
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
from tempfile import mkdtemp
from commands import getstatusoutput
from optparse import OptionParser, TitledHelpFormatter

USAGE = """benchbase [Options] FILE

  benchbase -j jmeter-bench-result.xml

"""

SCHEMAS = {
    # bench table
    'bench': {
        'md5sum': 'TEXT',   # md5sum of the file
        'filename': 'TEXT',  # imported filename
        'date': 'TEXT',  # date of import
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
    # benchbase table
    'cycles': {
        'bid': 'INTEGER',
        'cus': 'INTEGER',    # Concurrent users
        'start': 'INTEGER',  # start cycle
        'stop': 'INTEGER',   # end cycle
        'rowstart': 'INTEGER',  # first row
        'rowend': 'INTEGER',   # lastrow
        'count': 'INTEGER',   # number of sampler
        'duration': 'REAL'
        },
    'stats': {
        'bid': 'INTEGER',
        'cycle': 'INTEGER',   # cycle number
        'sampler': 'TEXT',    # label of the sampler or ALL
        'count': 'INTEGER',   # number of sampler
        'avg': 'REAL',
        'max': 'REAL',
        'min': 'REAL',
        'p10': 'REAL',
        'p50': 'REAL',
        'p90': 'REAL',
        'p95': 'REAL',
        'p98': 'REAL'
        }
}

CREATE_QUERY = 'CREATE TABLE IF NOT EXISTS [{table}]({fields})'
INSERT_QUERY = 'INSERT INTO {table} ({columns}) VALUES ({values})'
LOG_FILENAME = 'btracker.log'

DEFAULT_LOG = "~/benchbase.log"
DEFAULT_DB = "~/benchbase.db"


def get_version():
    """Retrun the FunkLoad package version."""
    from pkg_resources import get_distribution
    return get_distribution('benchbase').version


def md5sum(filename):
    f = open(filename)
    md5 = hashlib.md5()
    while True:
        data = f.read(8192)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()


def command(cmd, do_raise=True, verbose=False):
    """Return the status, output as a line list."""
    extra = 'LC_ALL=C '
    if verbose:
        print('Run: ' + extra + cmd)
    status, output = getstatusoutput(extra + cmd)
    if status:
        if do_raise:
            print('ERROR: [%s] return status: [%d], output: [%s]' %
                  (extra + cmd, status, output))
            raise RuntimeError('Invalid return code: %s' % status)
        else:
            if verbose:
                print ('return status: [%d]' % status)
    if output:
        output = output.split('\n')
    return (status, output)


def importJmeter(filename, options):
    md5 = md5sum(filename)
    print md5
    if options.rmdatabase and os.path.exists(options.database):
        print "Erasing existing database"
        logging.info("Erasing database: " + options.database)
        os.unlink(options.database)
    db = sqlite3.connect(options.database)

    table_names = SCHEMAS.keys()
    for table_name in table_names:
        sql_create = CREATE_QUERY.format(
            table=table_name,
            fields=", ".join(['{0} {1}'.format(name, type) for name, type in SCHEMAS[table_name].items()]))
        logging.info('Creating table {0}'.format(table_name))
        try:
            logging.info(sql_create)
            db.execute(sql_create)
        except Exception, e:
            logging.warning(e)
    c = db.cursor()
    t = (md5,)
    c.execute("SELECT * FROM bench WHERE md5sum = ? ", t)
    row = c.fetchone()
    if row:
        print "File already imported " + str(row)
        c.close()
        return

    t = (md5, filename, datetime.datetime.now())
    c.execute("INSERT INTO bench (md5sum, filename, date) VALUES (?, ?, ?)", t)
    c.close()

    logging.info("Processing JMeter file: {0}".format(filename))
    print "Processing JMeter file: " + filename
    with open(filename) as xml_file:
        tree = etree.iterparse(xml_file)
        for events, row in tree:
            table_name = row.tag.lower()
            if table_name not in table_names:
                continue
            try:
                logging.debug(row.attrib.keys())
                db.execute(INSERT_QUERY.format(
                        table=table_name,
                        columns=', '.join(row.attrib.keys()),
                        values=('?, ' * len(row.attrib.keys()))[:-2]),
                           row.attrib.values())
                print ".",
            except Exception, e:
                logging.warning(e)
                print "x",
            finally:
                row.clear()
        print "\n"
        db.commit()
        del(tree)
    # create time stamp
    db.execute("UPDATE sample SET stamp = ts/1000;")
    db.execute("UPDATE sample SET success = 1 WHERE s IN ('true', 'TRUE', 'True');")
    db.execute("UPDATE sample SET success = 0 WHERE s NOT IN ('true', 'TRUE', 'True');")

    # stats
    # Take in account cycles with sampler and longer than 5s
    db.execute("""INSERT INTO cycles SELECT na, min(stamp), max(stamp), COUNT(na), MIN(ROWID), MAX(ROWID), (MAX(ts) - MIN(ts))/1000.0 AS duration
    FROM sample
    WHERE na > 0
    GROUP BY na
    HAVING MAX(ts) - MIN(ts) > 5000
    ORDER BY stamp;""")
    db.commit()
    db.close()


# response time / s
#   select stamp, avg(t) from sample group by stamp;
# debit / s
# select datetime(stamp, 'unixepoch', 'localtime') DATE, na CUs, count(t), avg(t)/1000 from sample group by stamp;


def main():
    """Main test"""
    global USAGE
    parser = OptionParser(USAGE, formatter=TitledHelpFormatter(),
                          version="benchbase %s" % get_version())
    parser.add_option("-v", "--verbose", action="store_true",
                      help="Verbose output")
    parser.add_option("-o", "--output", type="string",
                      help="PNG output file")
    parser.add_option("-l", "--logfile", type="string",
                      default=os.path.expanduser(DEFAULT_LOG),
                      help="Log file path")
    parser.add_option("-d", "--database", type="string",
                      default=os.path.expanduser(DEFAULT_DB),
                      help="SQLite db path")
    parser.add_option("-j", "--jmeter", action="store_true",
                      default=True,
                      help="JMeter input file")
    parser.add_option("-f", "--funkload", action="store_true",
                      default=False,
                      help="FunkLoad input file")
    parser.add_option("--rmdatabase", action="store_true",
                      default=False,
                      help="Remove existing database")
    options, args = parser.parse_args(sys.argv)

    level = logging.INFO
    if options.verbose:
        level = logging.DEBUG
    logging.basicConfig(filename=options.logfile, level=level)

    if options.funkload:
        raise NotImplementedError("Sorry, not yet available.")
    if options.jmeter:
        if len(args) != 2:
            parser.error("Missing JMeter file")
            return
        importJmeter(args[1], options)
        return

if __name__ == '__main__':
    main()
