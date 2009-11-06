import openwns
import openwns.node
import openwns.distribution
import constanze.distribution.CDFTables

import constanze.traffic
import constanze.node
import constanze.evaluation.default

import ip.Component

import ip

import glue.support.Configuration

import copper.Copper

# create an instance of the WNS configuration
# The variable must be called WNS!!!!
WNS = openwns.Simulator(simulationModel = openwns.node.NodeSimulationModel())
WNS.outputStrategy = openwns.simulator.OutputStrategy.DELETE

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

class Station(openwns.node.Node):
    phy = None
    dll = None
    load = None
    logger = None

    def __init__(self, wire, ber, speed, id):
        super(Station, self).__init__("node"+str(id))
        # create Components in a Node
        self.logger = openwns.logger.Logger("CONST", "node"+str(id), True) # used for ConstanzeComponent
        self.phy = copper.Copper.Transceiver(self, "phy", wire, ber, speed)
        self.dll = glue.support.Configuration.AcknowledgedModeShortCutComponent(self, "ShortCut", self.phy.dataTransmission, self.phy.notification)
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
    if ( i == 0 ):
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
                traffic = constanze.traffic.CBR0(startTime, throughputPerStation, meanPacketSize, duration=duration, parentLogger=logger)
            elif ( trafficindex == 1 ):
                traffic = constanze.traffic.Poisson(startTime, throughputPerStation, meanPacketSize, duration=duration, parentLogger=logger)
            else:
                assert "invalid traffic choice"
            startTime += phaseDuration # next traffic after some time
            dllBinding = constanze.node.DllBinding(WNS.simulationModel.nodes[i].dll.address, WNS.simulationModel.nodes[i].dll.name, logger)   
            WNS.simulationModel.nodes[i-1].load.addTraffic(dllBinding, traffic)
    # only node1 should listen (to traffic):
    if ( i == 1 ):
        dllListenerBinding = constanze.node.DllListenerBinding(WNS.simulationModel.nodes[i-1].dll.address, WNS.simulationModel.nodes[i-1].dll.name ,logger)
        listener = constanze.node.Listener(WNS.simulationModel.nodes[i-1].dll.unicastNotification, logger)
        print "Listener(",WNS.simulationModel.nodes[i-1].dll.unicastNotification,")"
        WNS.simulationModel.nodes[i-1].load.addListener(dllListenerBinding, listener)

glue.support.Configuration.ShortCut.loggerEnabled = False
glue.support.Configuration.ShortCutComponent.loggerEnabled = False
glue.support.Configuration.AcknowledgedModeShortCutComponent.loggerEnabled = False

constanze.evaluation.default.installEvaluation(WNS,
                                               maxPacketDelay = 0.0001,
                                               maxPacketSize = 16000,
                                               maxBitThroughput = 2* throughputPerStation,
                                               maxPacketThroughput = 2 * throughputPerStation/meanPacketSize,
                                               delayResolution = 1000,
                                               sizeResolution = 2000,
                                               throughputResolution = 10000)

openwns.setSimulator(WNS)
