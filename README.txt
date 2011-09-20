===========
benchbase
===========

NAME
----
benchbase - Store and manage JMeter or FunkLoad benchmark results.
            Produces detailed reports.

Visit https://github.com/bdelbosc/benchbase/wiki to see report examples.

USAGE
-----

  benchbase [--version] [--logfile=LOGFILE] [--database=DATABASE] COMMAND [OPTIONS] [ARGUMENT]

COMMANDS
~~~~~~~~~

  list
     List the imported benchmark in the database.

  info BID
     Give more information about the benchmark with the bid number (benchmark identifier).

  import [--jmeter|--funkload|--comment=COMMENT] FILE
     Import the benchmark result into the database. Output the BID number. The input file can
     be gzipped.

  addsar --host HOST [--comment=COMMENT] BID SAR
     Import the text sysstat sar output, the input file can be gzipped.

  report --output REPORT_DIR BID
     Generate the report for the imported benchmark

EXAMPLES
~~~~~~~~~

   benchbase list
      List of imported benchmarks.

   benchbase import -m"Run 42" jmeter-2010.xml
      Import a JMeter benchmark result file, this will output a BID number.

   benchbase addsar -H"localhost" -m"bencher host" 1 /tmp/sysstat-sar.log.gz
      Attach a gzipped sysstat sar file for the bench BID 1.

   benchbase report 1 -o /tmp/report-run42
      Build the report of benchmark BID 1 into /tmp/report-run42 directory.


REQUIRES
--------

Benchbase requires `gnuplot <http://www.gnuplot.info/>`_ and sqlite3, on Debian/Ubuntu::
 
  sudo aptitude install sqlite3 gnuplot


INSTALLATION
------------
::

   sudo easy_install benchbase


INPUTS
--------

JMeter
~~~~~~~

Supported JMeter file format is JTL 2.1 sample attributes.

This has been tested using an ant script with the following configuration:
::

     <jmeter ...>
      ...
      <property name="file_format.testlog" value="2.1"/>
      <property name="jmeter.save.saveservice.output_format" value="xml"/>
      <property name="jmeter.save.saveservice.bytes" value="true"/>
      <property name="jmeter.save.saveservice.thread_counts" value="true"/>
      ...
     </jmeter>


The CSV output is also supported in 10 or 12 columns
::

    10: ['ts', 't', 'lb', 'tn', 'de', 's', 'by', 'ng', 'na', 'lt'],
    12: ['ts', 't', 'lb', 'rc', 'rm', 'tn', 'de', 's', 'by', 'ng', 'na', 'lt']}


FunkLoad
~~~~~~~~~~~

Should work with any FunkLoad xml result file.

Sysstat sar file
~~~~~~~~~~~~~~~~~~~

Supported sysstat sar format is the text output. For instance you can
capture stuff like this:

::

    sar -d -o /tmp/sar.data 1 100 > /dev/null 2>&1 &


This gets stats every second during 100s and store the result in a file.

To get the text output you need to run this:
 
::

    LC_ALL=C sar -f /tmp/sar.data -A > /tmp/sar.log

