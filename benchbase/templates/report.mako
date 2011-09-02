===================
Bench base report
===================

:abstract: ${comment}

.. sectnum::    :depth: 2
.. contents:: Table of contents


Bench configuration
-------------------

* Launched: ${start}, end: ${end}
* Duration: ${duration}s
* Maximum number of threads: ${maxThread}
* Load test tool: ${generator}
* Imported into benchbase: ${imported}
* From file: ${filename}

Bench summary
---------------

 =============== ========== ========== ============ ============= =========== ============ ====================
 Sample name     Samples    Failures   Success Rate  Average Time  Min Time    Max Time     Average Troughput
 --------------- ---------- ---------- ------------ ------------- ----------- ------------ --------------------
 ${"ALL             %10d %10d %11.2f%% %11.3fs %10.3fs %12.3fs %7.3f" % (count, error, (100. - (error * 100. / count)), avgt, mint, maxt, count / (1.0 * duration))}
 =============== ========== ========== ============ ============= =========== ============ ====================
% for name, sample in samples.items():
 ${"%-15s %10d %10d %11.2f%% %11.3fs %10.3fs %12.3fs %7.3f" % (name, sample['count'], sample['error'], (100. - (sample['error'] * 100. / sample['count'])), sample['avgt'], sample['mint'], sample['maxt'], sample['count'] / (1.0 * sample['duration']))}
% endfor
 =============== ========== ========== ============ ============= =========== ============ ====================



All samples
------------------------

 .. image:: global.png


Samples
----------

% for sample in samples:

${sample}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

 .. image:: ${sample}.png

% endfor



