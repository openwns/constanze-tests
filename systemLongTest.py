#! /usr/bin/env python2.4

# this is needed, so that the script can be called from everywhere
import os
import sys
base, tail = os.path.split(sys.argv[0])
os.chdir(base)

# Append the python sub-dir of WNS--main--x.y ...
sys.path.append(os.path.join('..', '..', '..', 'sandbox', 'default', 'lib', 'python2.4', 'site-packages'))

# ... because the module WNS unit test framework is located there.
import pywns.WNSUnit

# start manually with: cd /tests/system/Constanze-Tests--main--1.0; ./fast-wns-core -f constanzeTestsGlueLong.py
testSuite1 = pywns.WNSUnit.ProbesTestSuite(sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                    executeable = "wns-core",
                                    configFile = 'constanzeTestsGlueLong.py',
                                    shortDescription = 'All kinds of Constanze traffic sent over Copper, Glue, IP',
				    #runSimulations = False, # no wns-core, just probes and postprocessing
				    requireReferenceOutput = False,
				    #readProbes = True,
                                    disabled = False,
                                    disabledReason = "")

### This makes some nice output graphs to show what the different traffic is like:
# /fast-wns-core -f long_run.py

# create a system test
testSuite = pywns.WNSUnit.TestSuite()
testSuite.addTest(testSuite1)

#someExpectation = pywns.WNSUnit.Expectation("ip.endToEnd.packet.incoming.delay_SC1_PDF.dat",
#                                      ["probe.trials > 20000","probe.trials < 50000"],
#                                      "dbg")
#testSuite1.addTest(someExpectation)

# see ../../../framework/PyWNS--main--1.0/pywns/WNSUnit.py 
#somePostProcessing = pywns.WNSUnit.ExternalProgram(dirname = ".", command = "./output_rate_table", description = "PostProcessing with GnuPlot", includeStdOut = True)
# this produces a *.ps and *.png file with results:
#somePostProcessing = pywns.WNSUnit.ExternalProgram(dirname = ".", command = "./makeRateTableGraphs", description = "PostProcessing with GnuPlot", includeStdOut = True)
# only constanzeTestsGlue produces the right probes for postprocessing
#testSuite1.addTest(somePostProcessing)
# ^ if this command fails (exitcode>0), the test fails, showing that the tool chain does no longer work.
#print "WNS.outputDir=",WNS.outputDir

if __name__ == '__main__':
    # This is only evaluated if the script is called by hand

    # if you need to change the verbosity do it here
    verbosity = 2

    pywns.WNSUnit.verbosity = verbosity

    # Create test runner
    testRunner = pywns.WNSUnit.TextTestRunner(verbosity=verbosity)

    # Finally, run the tests.
    testRunner.run(testSuite)
    #testRunner.run(testSuite1)
    #testRunner.run(testSuite2)

