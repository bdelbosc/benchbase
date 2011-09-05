===========
benchbase
===========

NAME
----
benchbase - Store and manage JMeter or FunkLoad benchmark results.
            Produces detail reports

USAGE
-----

  benchbase [--version] [--logfile=LOGFILE] [--database=DATABASE] COMMAND [OPTIONS] [ARGUMENT]

COMMANDS
~~~~~~~~~

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
~~~~~~~~~

   benchbase list
      List of imported benchmarks.

   benchbase import -m"Tir 42" jmeter-2010.xml
      Import a JMeter benchmark result file.

   benchbase add --host localhost -m"bencher host" 12 /tmp/sysstat-sar.log

   benchbase report 12 -o /tmp/report-tir43
      Build the report of benchmark bid 12 into /tmp/report-tir43 directory


REQUIRES
--------

Benchbase requires `gnuplot <http://www.gnuplot.info/>`_ and sqlite3, on Debian/Ubuntu::
 
  sudo aptitude install sqlite3 gnuplot


INSTALLATION
------------
::

   sudo easy_install benchbase


NOTES
--------

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


Supported sysstat sar format is the text output. For instance you can
capture stuff like this:

::
    sar -d -o /tmp/sar.data 1 100 > /dev/null 2>&1 &


This gets stats every second during 100s and store the result in a file.

To get the text output you need to run this:
 
::
    LC_ALL=C sar -f /tmp/sar.data -A > /tmp/sar.log

