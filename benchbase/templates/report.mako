===================
Bench base report
===================

:abstract: ${comment}

.. sectnum::    :depth: 2
.. contents:: Table of contents

<%
f1 = "%20.20s %13.13s %13.13s %13.13s %13.13s %13.13s %13.13s %13.13s %13.13s %13.13s %13.13s %13.13s %13.13s %13.13s %13.13s"
f2 = "{title:<20} {count:>13} {error:>13} {success_rate:>13.2f} {avgt:>13.3f} {stddevt:>13.3f} {mint:>13.3f} {medt:>13.3f} {p90t:>13.3f} {p95t:>13.3f} {p98t:>13.3f} {maxt:>13.3f} {tput:>13.3f} {total:>13.2f} {percent:>13.2f}"
tb = f1 % (15 * ('=========================',))
th = f1 % (15 * ('-------------------------',))
tt = f1 % ('Sample name', 'Samples', 'Failures', 'Success Rate', 'Average time', 'Std dev', 'Min', 'Median', 'P90', 'P95', 'P98', 'Max', 'Avg Througput', 'Total time', '% Total time')
%>

Bench configuration
-------------------

* Launched: ${start}, end: ${end}
* Duration: ${duration}s
* Maximum number of threads: ${max_thread}
* Load test tool: ${generator}
* Imported into benchbase: ${imported}
* From file: ${filename}
% if generator.lower() == 'funkload':
* FunkLoad config:

  * Target url: ${extra.get('server_url')}
  * From node: ${extra.get('node')}
  * Test: ${extra.get('module')}.${extra.get('class')}.${extra.get('method')}
  * Description: ${extra.get('description')}
  * Cycles: ${extra.get('cycles')}
  * Cycle duration: ${extra.get('duration')}s
  * Sleep time between: ${extra.get('sleep_time_min')}s and ${extra.get('sleep_time_max')}s

## % for key, value in extra.items():
##  * ${key}: ${value}
## % endfor
% endif


Bench summary
---------------

${tb}
${tt}
${th}
${f2.format(**all_samples)}
${tb}
% for sample in samples:
${f2.format(**sample)}
% endfor
${tb}

% if len(sar):
Monitoring
-------------

% for host, komment in sar.items():

${host}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Host description: ${komment}

 .. image:: sar-${host}.png

% endfor

% endif


All samples
------------------------

${tb}
${tt}
${tb}
${f2.format(**all_samples)}
${tb}

 .. image:: all.png


Samples ordered by total time
------------------------------

% for sample in samples:

${sample['name']}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

${tb}
${tt}
${tb}
${f2.format(**sample)}
${tb}

 .. image:: ${sample['filename']}.png

% endfor

