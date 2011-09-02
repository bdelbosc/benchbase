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
* Imported into benchbase: ${imported}


Bench summary
---------------

 =============== ========== ========== ============ ============= =========== ============ ====================
 Sample name     Samples    Failure    Success Rate  Average Time  Min Time    Max Time     Average Troughput
 --------------- ---------- ---------- ------------ ------------- ----------- ------------ --------------------
 ${"ALL             %10d %10d %11.2f%% %11.3fs %10.3fs %12.3fs %7.3f" % (count, error, (100. - (error * 100. / count)), avgt, mint, maxt, count / (1.0 * duration))}
 =============== ========== ========== ============ ============= =========== ============ ====================
% for sample in samples:
 ${"%-15s" % sample} ${"%10d" % count} ${"%10d" % error}   ${"%9.2f" % (100. - (error * 100. / count))}%
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



