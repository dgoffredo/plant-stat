set xdata time
set timefmt '%Y-%m-%dT%H:%M:%SZ'

set y2tics

set xlabel 'Time (UTC)' offset 0,-1
set ylabel 'Temperature (°C)'
set y2label 'Relative Humidity (%)'

# Give the legend a solid background, and make sure that the border of the
# graph isn't drawn over it.
set key center top box opaque
set border back

set title 'Temperature and Relative Humidity versus Time'

# set terminal pngcairo nocrop enhanced size 1024,768
set terminal pngcairo background "#ffffff" enhanced fontscale 1.0 size 1024,768
set output output_file

plot 'dump.txt' using 1:2 title 'Temperature (°C) [left axis]' axes x1y1, \
     'dump.txt' using 1:3 title 'Relative Humidity (%) [right axis]' axes x1y2

