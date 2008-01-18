./systemTest.py in this directory now executes the tests
which were formerly in constanzeTestsGlue.py and constanzeTestsSimpleTL

Both generate a number (~10) of different traffic streams one after each other.

There is a 3rd Python configuration in long_run.py which you can call with
./fast-wns-core -f constanzeTestsGlueLong.py

This generates output long enough to see the nice graph traffic rate over time.
The r=f(t) graph can be generated fastly by
./plot_rate_table
and
gnuplot
with
gnuplot> load 'plotvectors.gnuplot'
afterwards.

or faster:

./makeRateTableGraphs
$viewerprogram graphs.junk/rate_output.png
