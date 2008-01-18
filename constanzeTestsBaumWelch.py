### constanzeTestsBaumWelch
# Constanze over IP (layer3) and Glue as DLL (layer2)
#
# use script ./output_rate_table in the current directory for a nice table
# use script ./makeRateTableGraphs in the current directory for nice graphs in ./graphs.junk/
#
#
import os

import wns.WNS
import wns.EventScheduler
import wns.Node
import wns.Distribution
import wns.distribution.CDFTables

import constanze.Constanze
import constanze.Node

import ip.Component

import ip

import glue.support.Configuration

import copper.Copper
from ip.VirtualARP import VirtualARPServer
from ip.VirtualDHCP import VirtualDHCPServer
from ip.VirtualDNS import VirtualDDNSServer

import speetcl.probes.StatEval

# create an instance of the WNS configuration
# The variable must be called WNS!!!!
WNS = wns.WNS.WNS()
WNS.outputStrategy = wns.WNS.OutputStrategy.DELETE

WNS.maxSimTime = 100 # seconds (here: some ms for each traffic type)
# must be < 250 (otherwise IPAddress out of range)
numberOfStations = 2

wire = copper.Copper.Wire("theWire") # this name appears in logger output

# link speed = 1 MBit/s
speed = 1E6
# Traffic load
meanPacketSize = 500 * 8 # bits
loadFactor = 1.00
throughputPerStation = speed * loadFactor / numberOfStations
# Probes Rate=f(time):
timeWindow = 0.1 # used for probes in IPv4Component
# probe in IPv4Component must be changed from pdfEval to LogEval (done below)

# Open issues: how to use Probes
# wanted: traffic rate over time r=f(t)
# solution: see below (bottom)

class Station(wns.Node.Node):
    phy = None
    dll = None
    nl = None
    load = None
    logger = None

    def __init__(self, wire, ber, speed, id):
        super(Station, self).__init__("node"+str(id))
        # create Components in a Node
        self.logger = wns.Logger.Logger("CONST", "node"+str(id), True) # used for ConstanzeComponent
        self.phy = copper.Copper.Transceiver(self, "phy", wire, ber, speed)
        self.dll = glue.support.Configuration.AcknowledgedModeShortCutComponent(self, "ShortCut", self.phy.dataTransmission, self.phy.notification)
        self.nl = ip.Component.IPv4Component(self, "192.168.1."+str(id+1),"station"+str(id+1)+".wns.org",probeWindow = timeWindow)
        # ^ IPv4Component contains probes
        # see ~/src/intranet2/WNS--main--3.0/modules/nl/ip--unstable--1.2/PyConfig/ip/Component.py

        self.nl.addDLL(_name = "glue",
                       _addressResolver = ip.Chains.VirtualDHCPResolver("theOnlySubnet"),
                       _arpZone = "theOnlySubnet",
                       _pointToPoint = False,
                       _dllDataTransmission = self.dll.unicastDataTransmission,
                       _dllNotification = self.dll.unicastNotification)
        # from ./modules/loadgen/Constanze--unstable--1.0/PyConfig/constanze/Node.py:
        self.load = constanze.Node.ConstanzeComponent(self, "constanze", self.logger)

# Create Nodes and components
for i in xrange(numberOfStations):
    #station = Station(wire, wns.Distribution.Fixed(0.000004), speed, i)
    # no packet error on the link:
    station = Station(wire, wns.Distribution.Fixed(0.0), speed, i)
    WNS.nodes.append(station)

MMPPoutputDir = './MMPPoutputDir.junk'
if (not os.access(MMPPoutputDir, os.F_OK)):
    os.mkdir(MMPPoutputDir)
# in this scenario we have only one listener, so it is Ok to have only one filename:
MMPPestimationResultFileName = os.path.join(MMPPoutputDir, "MMPPresult.py");

for i in xrange(numberOfStations):
    # WNS.nodes[i-1] is specified here...
    logger = WNS.nodes[i-1].logger
    # only node0 should generate traffic:
    if ( i == 1 ):

        startTime = 0.0
        #duration = 0.0 # [s], 0.0 means forever
        startindex = 0 # change to one of [0..10] to see other traffic first
        trafficVariants = 1
        phaseDuration = WNS.maxSimTime / trafficVariants
        #phaseDuration = 1.0 # [s]. Be sure that WNS.maxSimTime is long enough
        duration = phaseDuration - startTime

        mmppParams = constanze.Constanze.DTMMPPexample02()
        traffic = constanze.Constanze.DTMMPP(mmppParams, targetRate=throughputPerStation, slotTime = 1.0/10.0, offset = startTime, duration=duration, parentLogger = logger)
        traffic.logger.level = 3

        #startTime += phaseDuration # next traffic after some time
        #Node.py :: IPBinding(_destinationIP)

        ipBinding = constanze.Node.IPBinding(WNS.nodes[i-1].nl.domainName, WNS.nodes[i].nl.domainName, logger) # destination ip
        WNS.nodes[i-1].load.addTraffic(ipBinding, traffic)
        # for
    # only node1 should listen (to traffic):
    if ( i == 0 ):
        ipListenerBinding = constanze.Node.IPListenerBinding(WNS.nodes[i-1].nl.domainName, logger)
        measurement = constanze.Node.Measurement(MMPPestimationResultFileName=MMPPestimationResultFileName, estimatorNumberOfStates=5, meanRateList=[171272,342544,515880,685088,856360], probeWindow=timeWindow, logger=logger)
        listener = constanze.Node.Listener(WNS.nodes[i-1].nl.domainName + ".listener", logger, probeWindow=timeWindow, doMMPPestimation=True, measurement=measurement)
        WNS.nodes[i-1].load.addListener(ipListenerBinding, listener)


# one Virtual ARP Zone
varp = VirtualARPServer("VARP", "theOnlySubnet")

WNS.nodes.append(varp)

vdhcp = VirtualDHCPServer("VDHCP@",
                          "theOnlySubnet",
                          "192.168.0.2", "192.168.254.253",
                          "255.255.0.0")

vdns = VirtualDDNSServer("VDDNS", "ip.DEFAULT.GLOBAL")

WNS.nodes.append(vdns)

WNS.nodes.append(vdhcp)

glue.support.Configuration.ShortCut.loggerEnabled = False
glue.support.Configuration.ShortCutComponent.loggerEnabled = False
glue.support.Configuration.AcknowledgedModeShortCutComponent.loggerEnabled = False
wns.Logger.globalRegistry.enableLoggers("all", False)
wns.Logger.globalRegistry.enableLoggers("CONSTANZE", True)
wns.Logger.globalRegistry.setLoggerLevel("CONSTANZE", 2) # 2=normal, 3=verbose
#wns.Logger.globalRegistry.enableLoggers("GLUE", True)
#wns.Logger.globalRegistry.setLoggerLevel("GLUE", 2)

WNS.probesWriteInterval = 30 # in seconds realtime

# ~/src/intranet2/WNS--main--3.0/tests/constanzeTestsGlue: ../../framework/libwns--main--3.0/tools/pytree -p ../../sandbox/dbg/lib/PyConfig/ wns.py|more
WNS.modules.ip.probes['ip.endToEnd.window.incoming.bitThroughput'].sortingCriteria[0].statEvalSettings[0] = speetcl.probes.StatEval.LogEval()
WNS.modules.constanze.probes['traffic.endToEnd.window.incoming.bitThroughput'].sortingCriteria[0].statEvalSettings[0].maxXValue = 2* throughputPerStation
WNS.modules.constanze.probes['traffic.endToEnd.window.incoming.packetThroughput'].sortingCriteria[0].statEvalSettings[0].maxXValue = 2* throughputPerStation/meanPacketSize
#WNS.modules.constanze.probes['Traffic_windowedEndToEndIncomingBitThroughput'].sortingCriteria[0].statEvalSettings[0].maxXValue = 2* throughputPerStation
#WNS.modules.constanze.probes['Traffic_windowedEndToEndIncomingPacketThroughput'].sortingCriteria[0].statEvalSettings[0].maxXValue = 2* throughputPerStation/meanPacketSize
WNS.modules.constanze.probes['traffic.endToEnd.packet.incoming.delay'].sortingCriteria[0].statEvalSettings[0].maxXValue = 0.0001
WNS.modules.constanze.probes['traffic.endToEnd.packet.incoming.delay'].sortingCriteria[0].statEvalSettings[0].resolution = 1000
#WNS.modules.constanze.probes['Traffic_windowedEndToEndIncomingPacketThroughput'].sortingCriteria[0].statEvalSettings[0] = speetcl.probes.StatEval.LogEval()

#print "WNS.outputDir=",WNS.outputDir
graphdir = "graphs.junk"
if (not os.access(graphdir, os.F_OK)):
    os.mkdir(graphdir)
outputDirFile  = file('./outputDir.junk','w');  outputDirFile.write(WNS.outputDir); outputDirFile.close()
### postprocessing is specified in systemTest.py

# result Throughput=f(t) is in:
# output/IP_windowedEndToEndIncomingBitThroughput_SC1_Log.log.dat

# use this script to get a Gnuplot script and table:
# ./plot_rate_table

# HOWTO write a probe: see
# ~/src/intranet2/WNS--main--3.0/framework/speetcl--main--6.4/src/probe/tests/ProbeTest.cpp
