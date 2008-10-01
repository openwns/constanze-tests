### constanzeTestsGlue
#
# use script ./output_rate_table in the current directory for a nice table
#
#
import wns.WNS
import wns.EventScheduler
import wns.Node
import wns.Distribution
import constanze.distribution.CDFTables

import constanze.Constanze
import constanze.Node

import ip.Component

import ip

import glue.support.Configuration

import copper.Copper

#import speetcl.probes.StatEval

# create an instance of the WNS configuration
# The variable must be called WNS!!!!
WNS = wns.WNS.WNS()
WNS.outputStrategy = wns.WNS.OutputStrategy.DELETE

WNS.maxSimTime = 0.2 # seconds (here: some ms for each traffic type)

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
#timeWindow = 0.001 # used for probes in IPv4Component
# probe in IPv4Component must be changed from pdfEval to LogEval (done below)

# Open issues: how to use Probes
# wanted: traffic rate over time r=f(t)
# solution: see below (bottom)

class Station(wns.Node.Node):
    phy = None
    dll = None
    load = None
    logger = None

    def __init__(self, wire, ber, speed, id):
        super(Station, self).__init__("node"+str(id))
        # create Components in a Node
        self.logger = wns.Logger.Logger("CONST", "node"+str(id), True) # used for ConstanzeComponent
        self.phy = copper.Copper.Transceiver(self, "phy", wire, ber, speed)
        self.dll = glue.support.Configuration.AcknowledgedModeShortCutComponent(self, "ShortCut", self.phy.dataTransmission, self.phy.notification)
#        self.nl = ip.Component.IPv4Component(self, "192.168.1."+str(id+1),"192.168.1."+str(id+1), probeWindow = timeWindow)
        # ^ IPv4Component contains probes
        # see ~/src/intranet2/WNS--main--3.0/modules/nl/ip--unstable--1.2/PyConfig/ip/Component.py
#        self.nl.addDLL(self.dll.unicastDataTransmission, self.dll.unicastNotification)
#        ip.addToNeighbourCacheHelper(wire, self.dll, self.nl, "192.168.1." + str(id+1))
        # from ./modules/loadgen/Constanze--unstable--1.0/PyConfig/constanze/Node.py:
        self.load = constanze.Node.ConstanzeComponent(self, "constanze", self.logger)

# Create Nodes and components
for i in xrange(numberOfStations):
    #station = Station(wire, wns.Distribution.Fixed(0.000004), speed, i)
    # no packet error on the link:
    station = Station(wire, wns.Distribution.Fixed(0.0), speed, i)
    WNS.nodes.append(station)

#for i in xrange(numberOfStations):
#    WNS.nodes[i-1].nl.addNeighbour(
#        WNS.nodes[i].nl.address,
#        WNS.nodes[i-1].dll.unicastDataTransmission,
#        WNS.nodes[i].dll.address)

for i in xrange(numberOfStations):
    # WNS.nodes[i-1] is specified here...
    logger = WNS.nodes[i-1].logger
    # only node0 should generate traffic:
    print "i=",i
    if ( i == 1 ):
        #startTime = 0.001 # [s]
        startTime = 0.02 # [s]
        #duration = 0.0 # [s], 0.0 means forever
        startindex = 0 # change to one of [0..10] to see other traffic first
        trafficVariants = 2
        phaseDuration = WNS.maxSimTime / trafficVariants
        #phaseDuration = 1.0 # [s]. Be sure that WNS.maxSimTime is long enough
        duration = phaseDuration - startTime
        for trafficindexOffset in xrange(trafficVariants):
            trafficindex = (trafficindexOffset + startindex) % trafficVariants
            if ( trafficindex == 0 ):
                traffic = constanze.Constanze.CBR0(startTime, throughputPerStation, meanPacketSize, duration=duration, parentLogger=logger)
            elif ( trafficindex == 1 ):
                traffic = constanze.Constanze.Poisson(startTime, throughputPerStation, meanPacketSize, duration=duration, parentLogger=logger)
            else:
                assert "invalid traffic choice"
            startTime += phaseDuration # next traffic after some time
            # Node.py :: IPBinding(_destinationIP)
#            ipBinding = constanze.Node.IPBinding(WNS.nodes[i].nl.address, logger) # destination ip
            dllBinding = constanze.Node.DllBinding(WNS.nodes[i].dll.address, WNS.nodes[i].dll.name, logger) # destination MAC Address
            print "DllBinding(",WNS.nodes[i].dll.address,",", WNS.nodes[i].dll.name,")"
            WNS.nodes[i-1].load.addTraffic(dllBinding, traffic)
        # for
    # only node1 should listen (to traffic):
    if ( i == 2 ):
        #ipListenerBinding = constanze.Node.IPListenerBinding(WNS.nodes[i-1].nl.address, logger)
        dllListenerBinding = constanze.Node.DllListenerBinding(WNS.nodes[i-1].dll.address, WNS.nodes[i-1].dll.name ,logger)
        print "DllListenerBinding(",WNS.nodes[i-1].dll.address,",", WNS.nodes[i-1].dll.name,")"
        #listener = constanze.Node.Listener(WNS.nodes[i-1].nl.address + ".listener", logger, probeWindow=timeWindow)
        #listener = constanze.Node.Listener(str(WNS.nodes[i-1].dll.address ) + ".listener", logger, probeWindow=timeWindow)
        #listener = constanze.Node.Listener(WNS.nodes[i-1].dll.unicastNotification, logger, probeWindow=timeWindow)
        listener = constanze.Node.Listener(WNS.nodes[i-1].dll.unicastNotification, logger)
        print "Listener(",WNS.nodes[i-1].dll.unicastNotification,")"
        WNS.nodes[i-1].load.addListener(dllListenerBinding, listener)

glue.support.Configuration.ShortCut.loggerEnabled = False
glue.support.Configuration.ShortCutComponent.loggerEnabled = False
glue.support.Configuration.AcknowledgedModeShortCutComponent.loggerEnabled = False

