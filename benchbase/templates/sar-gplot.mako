set output "sar-${host}.png"
set terminal png size 640,768
set multiplot layout 3, 1 title "${host} sar monitoring"
set grid back
set xdata time
set timefmt "%H:%M:%S"
set format x "%H:%M"
set datafile separator "|"
set style data lines

set yrange [0:100]
set xrange ["${start}":"${end}"]

set title "CPU" offset 0, -2
set ylabel "%"
plot "< sqlite3 ${dbpath}  \"SELECT date, sys, usr, iowait, steal, nice FROM cpu WHERE bid = ${bid} ${filter} ORDER BY date\"" u 1:2 t 'sys', "" u 1:3 t 'usr', "" u 1:4 t 'iowait', "" u 1:5 t 'steal', "" u 1:6 t 'nice'

set title "CPU idle" offset 0, -2
set ylabel "%"
plot "< sqlite3 ${dbpath}  \"SELECT date, idle FROM cpu WHERE bid = ${bid} ${filter} ORDER BY date\"" u 1:2 t 'idle' lt 3, "" u 1:2 t 'bezier' lw 2 smooth bezier

set title "Disk usage" offset 0, -2
set ylabel "%"
plot "< sqlite3 ${dbpath}  \"SELECT date, MAX(util) FROM disk WHERE bid = ${bid} ${filter} GROUP BY date ORDER BY date\"" u 1:2 t 'usage', "" u 1:2 t 'bezier' lw 2 smooth bezier


unset multiplot

