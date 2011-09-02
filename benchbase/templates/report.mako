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


Bench content
---------------

* Number of samples: ${count}
* Samples in error: ${error}
* Percent of errors: ${"%.2f" % (error * 100. / count)} %
* List of samples

% for sample in samples:
  - ${sample}
% endfor


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



