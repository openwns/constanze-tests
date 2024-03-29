### constanzeTestsGlueLong
# Constanze over IP (layer3) and Glue as DLL (layer2)
#
# use script ./output_rate_table in the current directory for a nice table
# use script ./makeRateTableGraphs in the current directory for nice graphs in ./graphs.junk/
#
#
import os
import commands

import openwns
import openwns.node
import openwns.logger
import openwns.distribution
import constanze.distribution.CDFTables

import constanze.traffic
import constanze.node
import constanze.evaluation.default

import ip.Component

import ip
import ip.evaluation.default
import ip.AddressResolver
from ip.VirtualARP import VirtualARPServer
from ip.VirtualDHCP import VirtualDHCPServer
from ip.VirtualDNS import VirtualDNSServer

import glue.support.Configuration

import copper.Copper

from openwns.evaluation import *


# create an instance of the WNS configuration
# The variable must be called WNS!!!!
WNS = openwns.Simulator(simulationModel = openwns.node.NodeSimulationModel())
WNS.outputStrategy = openwns.simulator.OutputStrategy.DELETE

WNS.maxSimTime = 12.0 # seconds (here: some ms for each traffic type)

# must be < 250 (otherwise IPAddress out of range)
numberOfStations = 2

wire = copper.Copper.Wire("theWire") # this name appears in logger output

# link speed = 1 GBit/s
speed = 1E9
# Traffic load
meanPacketSize = 500 * 8 # bits
loadFactor = 0.1
throughputPerStation = speed * loadFactor / numberOfStations
# Probes Rate=f(time):
timeWindow = 0.001 # used for probes in IPv4Component
# probe in IPv4Component must be changed from pdfEval to LogEval (done below)

# Open issues: how to use Probes
# wanted: traffic rate over time r=f(t)
# solution: see below (bottom)

class Station(openwns.node.Node):
    phy = None
    dll = None
    nl = None
    load = None
    logger = None

    def __init__(self, wire, ber, speed, id):
        super(Station, self).__init__("node"+str(id))
        # create Components in a Node
        self.logger = openwns.logger.Logger("CONST", "node"+str(id), True) # used for ConstanzeComponent
        self.phy = copper.Copper.Transceiver(self, "phy", wire, ber, speed)
        self.dll = glue.support.Configuration.AcknowledgedModeShortCutComponent(self, "ShortCut", self.phy.dataTransmission, self.phy.notification)
        self.nl = ip.Component.IPv4Component(self, "192.168.1."+str(id+1),"station"+str(id+1)+".wns.org", probeWindow = timeWindow)
        # ^ IPv4Component contains probes
        # see ~/src/intranet2/WNS--main--3.0/modules/nl/ip--unstable--1.2/PyConfig/ip/Component.py
        self.nl.addDLL(_name = "glue",
                       _addressResolver = ip.AddressResolver.VirtualDHCPResolver("theOnlySubnet"),
                       _arpZone = "theOnlySubnet",
                       _pointToPoint = False,
                       _dllDataTransmission = self.dll.unicastDataTransmission,
                       _dllNotification = self.dll.unicastNotification)
        # from ./modules/loadgen/Constanze--unstable--1.0/PyConfig/constanze/Node.py:
        self.load = constanze.node.ConstanzeComponent(self, "constanze", self.logger)

# Create Nodes and components
for i in xrange(numberOfStations):
    #station = Station(wire, openwns.distribution.Fixed(0.000004), speed, i)
    # no packet error on the link:
    station = Station(wire, openwns.distribution.Fixed(0.0), speed, i)
    WNS.simulationModel.nodes.append(station)

for i in xrange(numberOfStations):
    # WNS.simulationModel.nodes[i-1] is specified here...
    logger = WNS.simulationModel.nodes[i-1].logger
    # only node0 should generate traffic:
    if ( i == 1 ):
        #startTime = 0.001 # [s]
        startTime = 0.2 # [s]
        #duration = 0.0 # [s], 0.0 means forever
        startindex = 0 # change to one of [0..10] to see other traffic first
        trafficVariants = 12
        phaseDuration = WNS.maxSimTime / trafficVariants
        #phaseDuration = 1.0 # [s]. Be sure that WNS.maxSimTime is long enough
        duration = phaseDuration - startTime
        for trafficindexOffset in xrange(trafficVariants):
            trafficindex = (trafficindexOffset + startindex) % trafficVariants
            if ( trafficindex == 0 ):
                traffic = constanze.traffic.CBR0(startTime, throughputPerStation, meanPacketSize, duration=duration, parentLogger=logger)
            elif ( trafficindex == 1 ):
                traffic = constanze.traffic.Poisson(startTime, throughputPerStation, meanPacketSize, duration=duration, parentLogger=logger)
            elif ( trafficindex == 2 ):
                iatDistribution = openwns.distribution.Fixed(meanPacketSize / throughputPerStation) # arg is mean interarrival time [s]
                #packetSizeDistribution = openwns.distribution.Fixed(meanPacketSize)
                packetSizeDistribution = openwns.distribution.Uniform(2*meanPacketSize,8)
                traffic = constanze.traffic.ABR(iatDistribution, packetSizeDistribution, offset = startTime, duration=duration, parentLogger = logger)
            elif ( trafficindex == 3 ):
                IPmeanPacketSize = 2056.84 # Bits
                iatDistribution = openwns.distribution.NegExp(IPmeanPacketSize / throughputPerStation) # arg is mean interarrival time [s]
                packetSizeDistribution = constanze.distribution.CDFTables.IPPacketSizeDataTraffic()
                traffic = constanze.traffic.ABR(iatDistribution, packetSizeDistribution, offset = startTime, duration=duration, parentLogger = logger)
            elif ( trafficindex == 4 ):
                mmppParams = constanze.traffic.MMPPparamsFromFile("mmpp_example.gdf")
                traffic = constanze.traffic.MMPP(mmppParams, numberOfChains=1, targetRate=throughputPerStation, transitionScale=0.1, offset = startTime, duration=duration, parentLogger = logger)
            elif ( trafficindex == 5 ):
                mmppParams = constanze.traffic.MMPPexampleONOFF()
                traffic = constanze.traffic.MMPP(mmppParams, targetRate=throughputPerStation, transitionScale=1.0, offset = startTime, duration=duration, parentLogger = logger)
            elif ( trafficindex == 6 ):
                mmppParams = constanze.traffic.MMPPMPEG2()
                traffic = constanze.traffic.MMPP(mmppParams, targetRate=throughputPerStation, transitionScale=5.0, offset = startTime, duration=duration, parentLogger = logger)
            elif ( trafficindex == 7 ):
                mmppParams = constanze.traffic.MMPPdata()
                #traffic = constanze.traffic.MMPP(mmppParams, rateScale=0.5, transitionScale=1.0, offset = startTime,duration=duration, parentLogger = logger)
		traffic = constanze.traffic.MMPP(mmppParams, targetRate=throughputPerStation, transitionScale=1.0, offset = startTime, duration=duration, parentLogger = logger)
            elif ( trafficindex == 8 ):
                # construct MMPP traffic manually (this is how to do it):
                numberOfStates=2
                matrix = ((0.0, 100.0),(100.0, 0.0))
                iatDistribution = [ openwns.distribution.Fixed(1e-3), openwns.distribution.NegExp(100e-6) ]
                packetSizeDistribution = [ openwns.distribution.Fixed(128), openwns.distribution.Fixed(meanPacketSize) ]
                stateList = []
                for stateindex in xrange(numberOfStates):
                    stateParam = constanze.traffic.MMPPstateParams(iatDistribution[stateindex], packetSizeDistribution[stateindex])
                    stateList.append(stateParam)
                mmppParams = constanze.traffic.MMPPparamsComplete(numberOfChains=1,
                                                                    numberOfStates=numberOfStates,
                                                                    transitionMatrix=matrix,
                                                                    stateList=stateList)
                #traffic = constanze.traffic.MMPP(mmppParams, rateScale=1.0, transitionScale=1.0, offset = startTime, duration=duration, parentLogger = logger)
		traffic = constanze.traffic.MMPP(mmppParams, targetRate=throughputPerStation, transitionScale=1.0, offset = startTime, duration=duration, parentLogger = logger)
            elif ( trafficindex == 9 ):
                mmppParams = constanze.traffic.DTMMPPexample01()
                traffic = constanze.traffic.DTMMPP(mmppParams, targetRate=throughputPerStation, slotTime = 1.0/10000.0, offset = startTime, duration=duration, parentLogger = logger)
                #traffic.logger.level = 3
            elif ( trafficindex == 10 ):
                mmppParams = constanze.traffic.DTMMPPMPEG2()
                traffic = constanze.traffic.DTMMPP(mmppParams, targetRate=throughputPerStation, slotTime = 1.0/300.0, offset = startTime, duration=duration, parentLogger = logger)
                #traffic.logger.level = 3
            elif ( trafficindex == 11 ):
                traffic = constanze.traffic.SelfSimilar(targetRate=throughputPerStation, offset = startTime, duration=duration, parentLogger = logger)
                #mmppParams = constanze.traffic.MMPPSelfSimilar()
                #traffic = constanze.traffic.MMPP(mmppParams, targetRate=throughputPerStation, offset = startTime, duration=duration, parentLogger = logger)
                #traffic.logger.level = 3
            else:
                assert "invalid traffic choice"
            startTime += phaseDuration # next traffic after some time
            # Node.py :: IPBinding(_destinationIP)
            ipBinding = constanze.node.IPBinding(WNS.simulationModel.nodes[i-1].nl.domainName, WNS.simulationModel.nodes[i].nl.domainName, logger) # destination ip
            WNS.simulationModel.nodes[i-1].load.addTraffic(ipBinding, traffic)
        # for
    # only node1 should listen (to traffic):
    if ( i == 0 ):
        ipListenerBinding = constanze.node.IPListenerBinding(WNS.simulationModel.nodes[i-1].nl.domainName, logger)
        listener = constanze.node.Listener(WNS.simulationModel.nodes[i-1].nl.domainName + ".listener", logger, probeWindow=timeWindow)
        WNS.simulationModel.nodes[i-1].load.addListener(ipListenerBinding, listener)

# one Virtual ARP Zone
varp = VirtualARPServer("vARP", "theOnlySubnet")

WNS.simulationModel.nodes.append(varp)

vdhcp = VirtualDHCPServer("vDHCP@",
                          "theOnlySubnet",
                          "192.168.0.2", "192.168.254.253",
                          "255.255.0.0")

vdns = VirtualDNSServer("vDNS", "ip.DEFAULT.GLOBAL")

WNS.simulationModel.nodes.append(vdns)

WNS.simulationModel.nodes.append(vdhcp)


glue.support.Configuration.ShortCut.loggerEnabled = False
glue.support.Configuration.ShortCutComponent.loggerEnabled = False
glue.support.Configuration.AcknowledgedModeShortCutComponent.loggerEnabled = False

WNS.probesWriteInterval = 30 # in seconds realtime

constanze.evaluation.default.installEvaluation(WNS,
                                               maxPacketDelay = 0.0001,
                                               maxPacketSize = 16000,
                                               maxBitThroughput = 2* throughputPerStation,
                                               maxPacketThroughput = 2 * throughputPerStation/meanPacketSize,
                                               delayResolution = 1000,
                                               sizeResolution = 2000,
                                               throughputResolution = 10000)

ip.evaluation.default.installEvaluation(WNS,
                                        maxPacketDelay = 0.5,     # s
                                        maxPacketSize = 2000*8,   # Bit
                                        maxBitThroughput = 10E6,  # Bit/s
                                        maxPacketThroughput = 1E6 # Packets/s
                                        )

WNS.probeBusRegistry.removeMeasurementSourceNode('ip.endToEnd.window.incoming.bitThroughput')
node = openwns.evaluation.createSourceNode(WNS, 'ip.endToEnd.window.incoming.bitThroughput')
node.appendChildren(TimeSeries())

openwns.setSimulator(WNS)

#def myPostProcessing(theWNSInstance):
#        graphdir = "graphs.junk"
#        if (not os.access(graphdir, os.F_OK)):
#            os.mkdir(graphdir)
#        outputDirFile  = file('./outputDir.junk','w');
#        outputDirFile.write(theWNSInstance.outputDir);
#        outputDirFile.close()# ^ needed for postprocessing with ./makeRateTableGraphs and ./output_rate_table
#        return True
#
#WNS.addPostProcessing(myPostProcessing)

# result Throughput=f(t) is in:
# output/IP_windowedEndToEndIncomingBitThroughput_SC1_Log.log.dat

# use this script to get a Gnuplot script and table:
# ./plot_rate_table

# HOWTO write a probe: see
# ~/src/intranet2/WNS--main--3.0/framework/speetcl--main--6.4/src/probe/tests/ProbeTest.cpp
