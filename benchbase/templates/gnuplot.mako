set output "${output_dir}/${sample}.png"
set terminal png size 640,768
set multiplot layout 4, 1 title "${title}"
set grid back
set xdata time
set timefmt "%H:%M:%S"
set format x "%H:%M"
set datafile separator "|"
set style data lines

set title "Concurrent Users" offset 0, -2
set ylabel "Threads"
plot "< sqlite3 ${dbpath}  \"select time(stamp, 'unixepoch', 'localtime') TIME, na from sample where bid = ${bid} ${filter} group by stamp order by stamp\"" u 1:2 notitle with steps lw 2 lt 3
set title "Samples per second"
set ylabel "Samples"
plot "< sqlite3 ${dbpath}  \"select time(stamp, 'unixepoch', 'localtime') TIME, count(na) from sample where bid = ${bid} ${filter} group by stamp order by stamp\"" u 1:2 lt 3  notitle with steps, "" u 1:2 notitle with line lt 2 lw 2 smooth bezier 

set title "Average response time in second" offset 0, -2
set ylabel "Seconds"
plot "< sqlite3 ${dbpath}  \"select time(stamp, 'unixepoch', 'localtime') TIME, avg(t)/1000.0 from sample where bid = ${bid} ${filter} group by stamp order by stamp\"" u 1:2 lt 3 notitle with linespoints, "" u 1:2 notitle with line lw 2 lt 6 smooth bezier
set title "Errors per second"
set ylabel "Errors"
plot "< sqlite3 ${dbpath}  \"select time(stamp, 'unixepoch', 'localtime') TIME, COUNT(na) - SUM(success) from sample where bid = ${bid} ${filter} group by stamp order by stamp\"" u 1:2 notitle with steps lw 2

unset multiplot

