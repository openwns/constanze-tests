
# gnuplot script to display vectors as graphic.
# to start, run gnuplot, then in gnuplot, type: 'load "plotvectors.gnuplot"'
#set term postscript;set output "plotvectors.gnuplot.ps"
set autoscale x;set autoscale y     #set various things to default.
set xtics;set ytics;set nokey;set nolabel
set nologscale y;set nologscale x
set grid;set nolabel
set title ""
# 			hier anpassen:
#set xrange [0:10]
#set yrange [0:1]
#set key 0.5,0.5
#set logscale y
set xlabel ""
set ylabel ""

set title "rate=f(t) TRAFFIC MIX"
set xlabel "t"
set ylabel "r(t)"
plot 'rate_output.table' u 1:2 w steps
pause -1 "Press a key !"
set term postscript;set output "trafficmix.ps"
plot 'rate_output.table' u 1:2 w steps
set term png;set output "trafficmix.png"
plot 'rate_output.table' u 1:2 w steps
set output; set term x11
set autoscale x;set autoscale y

set title "rate=f(t) MPEG2"
set xlabel "t"
set ylabel "r(t)"
plot 'rate_output.mpeg2.table' u 1:2 w steps
pause -1 "Press a key !"
set term postscript;set output "mpeg2.ps"
plot 'rate_output.mpeg2.table' u 1:2 w steps
set term png;set output "mpeg2.png"
plot 'rate_output.mpeg2.table' u 1:2 w steps
set output; set term x11
set autoscale x;set autoscale y

set title "rate=f(t) pareto"
set xlabel "t"
set ylabel "r(t)"
plot 'rate_output.pareto.table' u 1:2 w steps
pause -1 "Press a key !"
set term postscript;set output "pareto.ps"
plot 'rate_output.pareto.table' u 1:2 w steps
set term png;set output "pareto.png"
plot 'rate_output.pareto.table' u 1:2 w steps
set output; set term x11
set autoscale x;set autoscale y

set title "rate=f(t) pareto_t10c10"
set xlabel "t"
set ylabel "r(t)"
plot 'rate_output.pareto_t10c10.table' u 1:2 w steps
pause -1 "Press a key !"
set term postscript;set output "pareto_t10c10.ps"
plot 'rate_output.pareto_t10c10.table' u 1:2 w steps
set term png;set output "pareto_t10c10.png"
plot 'rate_output.pareto_t10c10.table' u 1:2 w steps
set output; set term x11
set autoscale x;set autoscale y
