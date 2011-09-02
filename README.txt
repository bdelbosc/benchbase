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

  report --output REPORT_DIR BID
     Generate the report for the imported benchmark

EXAMPLES
~~~~~~~~~

   benchbase list
      List of imported benchmarks.

   benchbase import -m"Tir 42" jmeter-2010.xml
      Import a JMeter benchmark result file.

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


