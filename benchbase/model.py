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
import sqlite3
import logging
from sqlitext import add_aggregates

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
    'j_testresults': {
        'bid': 'INTEGER',
        'version': 'TEXT'
        },
    # jmeter table
    'j_sample': {
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

    # FunkLoad tables
    'f_config': {
        'bid': 'INTEGER',
        'key': 'TEXT',
        'value': 'TEXT'
        },

    'f_response': {
        'bid': 'INTEGER',
        'stamp': 'INTEGER',    # timestamp in second
        'success': 'INTEGER',  # cast on s field
        'lb': 'TEXT',
        # fl fields
        'cycle': 'INTEGER',
        'cvus': 'INTEGER',
        'thread': 'INTEGER',
        'suite': 'TEXT',
        'name': 'TEXT',
        'step': 'INTEGER',
        'number': 'INTEGER',
        'type': 'TEXT',
        'result': 'TEXT',
        'url': 'TEXT',
        'code': 'INTEGER',
        'description': 'TEXT',
        'time': 'REAL',
        'duration': 'REAL'
        },

    'f_testresult': {
        'bid': 'INTEGER',
        'cycle': 'INTEGER',
        'cvus': 'INTEGER',
        'thread': 'INTEGER',
        'suite': 'TEXT',
        'name': 'TEXT',
        'time': 'REAL',
        'result': 'TEXT',
        'steps': 'INTEGER',
        'duration': 'REAL',
        'connection_duration': 'REAL',
        'requests': 'INTEGER',
        'pages': 'INTEGER',
        'xmlrpc': 'INTEGER',
        'redirects': 'INTEGER',
        'images': 'INTEGER',
        'links': 'INTEGER'
        }


}
CREATE_QUERY = 'CREATE TABLE IF NOT EXISTS [{table}]({fields})'
INSERT_QUERY = 'INSERT INTO {table} ({columns}) VALUES ({values})'


def open_db(options, create=True):
    if options.rmdatabase and os.path.exists(options.database):
        logging.warning("Erasing database: " + options.database)
        os.unlink(options.database)
        create = True
    db = sqlite3.connect(options.database)
    add_aggregates(db)
    if create:
        initialize_db(db)
    return db


def initialize_db(db):
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
    db.execute("create index if not exists j_stamp_idx on j_sample (stamp)")
    db.execute("create index if not exists f_response_idx on f_response (stamp)")
    db.commit()
    return db


def list_benchmarks(db):
    c = db.cursor()
    c.execute('SELECT ROWID, date, generator, filename, comment FROM bench')
    print "%5s %-19s %-8s %-30s %s" % ('bid', 'Imported', 'Tool', 'Filename', 'Comment')
    for row in c:
        print "%5d %19s %-8s %-30s %s" % (row[0], row[1][:19], row[2], os.path.basename(row[3]), row[4])
    c.close()
