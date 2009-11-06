### constanzeTestsSimpleTL
# Constanze over UDP and SimpleTL
import openwns
import openwns.logger
import openwns.qos

# import other modules to be loaded
import simpleTL.Component
import openwns.distribution
import constanze.distribution.CDFTables
import constanze.traffic
import constanze.node
import constanze.evaluation.default

# create an instance of the WNS configuration
# The variable must be called WNS!!!!
WNS = openwns.Simulator(simulationModel = openwns.node.NodeSimulationModel())
WNS.outputStrategy = openwns.simulator.OutputStrategy.DELETE
WNS.maxSimTime = 1.0

numberOfClients = 1
numberOfServers = 1
numberOfStations = numberOfClients

# link speed = 1 GBit/s
speed = 1E9
# Traffic load
meanPacketSize = 1500 * 8
loadFactor = 0.1
throughputPerStation = speed * loadFactor / numberOfStations

class ClientNode(openwns.node.Node):
    tl = None
    #applications = None
    load = None
    logger = None
    def __init__(self, id):
        super(ClientNode, self).__init__("client"+str(id))
        self.logger = openwns.logger.Logger("CONST", "client"+str(id), True) # used for ConstanzeComponent
        # create Components in a client node
        self.tl = simpleTL.Component.Component(self, "ClientTL", "127.0.0."+str(id+1))

        #self.applications = applications.Applications.Client(self, "ClientAppls", self.tl.TCP, self.tl.UDP)
        # type of traffic this client shall produce
	# TODO: add constanze component
	self.load = constanze.node.ConstanzeComponent(self, "constanze",self.logger)

class ServerNode(openwns.node.Node):
    tl = None
    #applications = None
    load = None
    logger = None
    def __init__(self, id):
        super(ServerNode, self).__init__("server"+str(id))
        self.logger = openwns.logger.Logger("CONST", "server"+str(id), True) # used for ConstanzeComponent
        # create Components in a server node
        self.tl = simpleTL.Component.Component(self, "ServerTL", "137.226.4."+str(id+1))
        #self.applications = applications.Applications.Server(self, "ServerAppls", self.tl.TCP, self.tl.UDP)
	self.load = constanze.node.ConstanzeComponent(self, "constanze",self.logger)

for i in xrange(numberOfServers):
    node = ServerNode(i)
    logger = node.logger
    udpListenerBinding = constanze.node.UDPListenerBinding(777, logger)
    udpListenerBinding.udpService = node.tl.udpServiceName
    listener = constanze.node.Listener("listener",logger);
    node.load.addListener(udpListenerBinding, listener)
    WNS.simulationModel.nodes.append(node)

serverNode = ServerNode(0)
for i in xrange(numberOfClients):
    node = ClientNode(i+numberOfServers)
    logger = node.logger
    startTime = 0.01 # [s]
    startindex = 0 # change to one of [0..7] to see other traffic first
    trafficVariants = 11
    phaseDuration = WNS.maxSimTime / trafficVariants
    #phaseDuration = 1.0 # [s]. Be sure that WNS.maxSimTime is long enough
    #duration = 0.0 # [s], 0.0 means forever
    duration = phaseDuration - startTime
    if ( True ):
        for trafficindexOffset in xrange(trafficVariants):
            trafficindex = (trafficindexOffset + startindex) % trafficVariants
            if ( trafficindex == 0 ):
                traffic = constanze.traffic.CBR(startTime, throughputPerStation, meanPacketSize, duration=duration, parentLogger=logger)
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
                traffic = constanze.traffic.MMPP(mmppParams, targetRate=throughputPerStation, transitionScale=1.0, offset = startTime, duration=duration, parentLogger = logger)
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
                #traffic.logger.level = 3
            else:
                assert "invalid traffic choice"
            startTime += phaseDuration # next traffic after some time
            # Node.py :: IPBinding(_destinationIP)
            #ipBinding = constanze.node.IPBinding(WNS.simulationModel.nodes[i].nl.address)
            #ipBinding = constanze.node.IPBinding(node.tl.IPAddress)
            udpBinding = constanze.node.UDPBinding(node.tl.domainName, serverNode.tl.domainName, 777, openwns.qos.undefinedQosClass, logger)
	    udpBinding.udpService = node.tl.udpServiceName
            #WNS.simulationModel.nodes[i-1].load.addTraffic(ipBinding, cbr) # from glueTests
            node.load.addTraffic(udpBinding, traffic)
        # for
    WNS.simulationModel.nodes.append(node)

constanze.evaluation.default.installEvaluation(WNS,
                                               maxPacketDelay = 0.0001,
                                               maxPacketSize = 16000,
                                               maxBitThroughput = 2* throughputPerStation,
                                               maxPacketThroughput = 2 * throughputPerStation/meanPacketSize,
                                               delayResolution = 1000,
                                               sizeResolution = 2000,
                                               throughputResolution = 10000)

openwns.setSimulator(WNS)

#print "WNS.outputDir=",WNS.outputDir
#graphdir = "graphs.junk"
#if (not os.access(graphdir, os.F_OK)):
#    os.mkdir(graphdir)
#outputDirFile  = file('./outputDir.junk','w');  outputDirFile.write(WNS.outputDir); outputDirFile.close()
### postprocessing is specified in systemTest.py

