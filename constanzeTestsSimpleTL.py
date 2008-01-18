### constanzeTestsSimpleTL
# Constanze over UDP and SimpleTL
import wns

# import other modules to be loaded
from speetcl.probes import ProbeModding
#import applications
import simpleTL.Component
import wns.Distribution
import wns.distribution.CDFTables
import constanze.Constanze
import constanze.Node
#import wns.Distribution

# create an instance of the WNS configuration
# The variable must be called WNS!!!!
WNS = wns.WNS.WNS()
WNS.outputStrategy = wns.WNS.OutputStrategy.DELETE
WNS.maxSimTime = 1.0
WNS.fastShutdown = False

# Activate all probes
#for (k,v) in appls.probes.items():
#    ProbeModding.doNotIgnore(v)

numberOfClients = 1
numberOfServers = 1
numberOfStations = numberOfClients

# link speed = 1 GBit/s
speed = 1E9
# Traffic load
meanPacketSize = 1500 * 8
loadFactor = 0.1
throughputPerStation = speed * loadFactor / numberOfStations

class ClientNode(wns.Node.Node):
    tl = None
    #applications = None
    load = None
    logger = None
    def __init__(self, id):
        super(ClientNode, self).__init__("client"+str(id))
        self.logger = wns.Logger.Logger("CONST", "client"+str(id), True) # used for ConstanzeComponent
        # create Components in a client node
        self.tl = simpleTL.Component.Component(self, "ClientTL", "127.0.0."+str(id+1))

        #self.applications = applications.Applications.Client(self, "ClientAppls", self.tl.TCP, self.tl.UDP)
        # type of traffic this client shall produce
	# TODO: add constanze component
	self.load = constanze.Node.ConstanzeComponent(self, "constanze",self.logger)

class ServerNode(wns.Node.Node):
    tl = None
    #applications = None
    load = None
    logger = None
    def __init__(self, id):
        super(ServerNode, self).__init__("server"+str(id))
        self.logger = wns.Logger.Logger("CONST", "server"+str(id), True) # used for ConstanzeComponent
        # create Components in a server node
        self.tl = simpleTL.Component.Component(self, "ServerTL", "137.226.4."+str(id+1))
        #self.applications = applications.Applications.Server(self, "ServerAppls", self.tl.TCP, self.tl.UDP)
	self.load = constanze.Node.ConstanzeComponent(self, "constanze",self.logger)

for i in xrange(numberOfServers):
    node = ServerNode(i)
    logger = node.logger
    udpListenerBinding = constanze.Node.UDPListenerBinding(777, logger)
    listener = constanze.Node.Listener("listener",logger);
    node.load.addListener(udpListenerBinding, listener)
    WNS.nodes.append(node)

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
                traffic = constanze.Constanze.CBR(startTime, throughputPerStation, meanPacketSize, duration=duration, parentLogger=logger)
            elif ( trafficindex == 1 ):
                traffic = constanze.Constanze.Poisson(startTime, throughputPerStation, meanPacketSize, duration=duration, parentLogger=logger)
            elif ( trafficindex == 2 ):
                iatDistribution = wns.Distribution.Fixed(meanPacketSize / throughputPerStation) # arg is mean interarrival time [s]
                #packetSizeDistribution = wns.Distribution.Fixed(meanPacketSize)
                packetSizeDistribution = wns.Distribution.Uniform(2*meanPacketSize,8)
                traffic = constanze.Constanze.ABR(iatDistribution, packetSizeDistribution, offset = startTime, duration=duration, parentLogger = logger)
            elif ( trafficindex == 3 ):
                IPmeanPacketSize = 2056.84 # Bits
                iatDistribution = wns.Distribution.NegExp(IPmeanPacketSize / throughputPerStation) # arg is mean interarrival time [s]
                packetSizeDistribution = wns.distribution.CDFTables.IPPacketSizeDataTraffic()
                traffic = constanze.Constanze.ABR(iatDistribution, packetSizeDistribution, offset = startTime, duration=duration, parentLogger = logger)
            elif ( trafficindex == 4 ):
                mmppParams = constanze.Constanze.MMPPparamsFromFile("mmpp_example.gdf")
                traffic = constanze.Constanze.MMPP(mmppParams, numberOfChains=1, targetRate=throughputPerStation, transitionScale=0.1, offset = startTime, duration=duration, parentLogger = logger)
            elif ( trafficindex == 5 ):
                mmppParams = constanze.Constanze.MMPPexampleONOFF()
                traffic = constanze.Constanze.MMPP(mmppParams, targetRate=throughputPerStation, transitionScale=1.0, offset = startTime, duration=duration, parentLogger = logger)
            elif ( trafficindex == 6 ):
                mmppParams = constanze.Constanze.MMPPMPEG2()
                traffic = constanze.Constanze.MMPP(mmppParams, targetRate=throughputPerStation, transitionScale=1.0, offset = startTime, duration=duration, parentLogger = logger)
            elif ( trafficindex == 7 ):
                mmppParams = constanze.Constanze.MMPPdata()
                #traffic = constanze.Constanze.MMPP(mmppParams, rateScale=0.5, transitionScale=1.0, offset = startTime,duration=duration, parentLogger = logger)
		traffic = constanze.Constanze.MMPP(mmppParams, targetRate=throughputPerStation, transitionScale=1.0, offset = startTime, duration=duration, parentLogger = logger)
            elif ( trafficindex == 8 ):
                # construct MMPP traffic manually (this is how to do it):
                numberOfStates=2
                matrix = ((0.0, 100.0),(100.0, 0.0))
                iatDistribution = [ wns.Distribution.Fixed(1e-3), wns.Distribution.NegExp(100e-6) ]
                packetSizeDistribution = [ wns.Distribution.Fixed(128), wns.Distribution.Fixed(meanPacketSize) ]
                stateList = []
                for stateindex in xrange(numberOfStates):
                    stateParam = constanze.Constanze.MMPPstateParams(iatDistribution[stateindex], packetSizeDistribution[stateindex])
                    stateList.append(stateParam)
                mmppParams = constanze.Constanze.MMPPparamsComplete(numberOfChains=1,
                                                                    numberOfStates=numberOfStates,
                                                                    transitionMatrix=matrix,
                                                                    stateList=stateList)
                #traffic = constanze.Constanze.MMPP(mmppParams, rateScale=1.0, transitionScale=1.0, offset = startTime, duration=duration, parentLogger = logger)
		traffic = constanze.Constanze.MMPP(mmppParams, targetRate=throughputPerStation, transitionScale=1.0, offset = startTime, duration=duration, parentLogger = logger)
            elif ( trafficindex == 9 ):
                mmppParams = constanze.Constanze.DTMMPPexample01()
                traffic = constanze.Constanze.DTMMPP(mmppParams, targetRate=throughputPerStation, slotTime = 1.0/10000.0, offset = startTime, duration=duration, parentLogger = logger)
                #traffic.logger.level = 3
            elif ( trafficindex == 10 ):
                mmppParams = constanze.Constanze.DTMMPPMPEG2()
                traffic = constanze.Constanze.DTMMPP(mmppParams, targetRate=throughputPerStation, slotTime = 1.0/300.0, offset = startTime, duration=duration, parentLogger = logger)
                #traffic.logger.level = 3
            elif ( trafficindex == 11 ):
                traffic = constanze.Constanze.SelfSimilar(targetRate=throughputPerStation, offset = startTime, duration=duration, parentLogger = logger)
                #traffic.logger.level = 3
            else:
                assert "invalid traffic choice"
            startTime += phaseDuration # next traffic after some time
            # Node.py :: IPBinding(_destinationIP)
            #ipBinding = constanze.Node.IPBinding(WNS.nodes[i].nl.address)
            #ipBinding = constanze.Node.IPBinding(node.tl.IPAddress)
            udpBinding = constanze.Node.UDPBinding(node.tl.domainName, serverNode.tl.domainName, 777, logger)
            #WNS.nodes[i-1].load.addTraffic(ipBinding, cbr) # from glueTests
            node.load.addTraffic(udpBinding, traffic)
        # for
    WNS.nodes.append(node)

#print "WNS.outputDir=",WNS.outputDir
#graphdir = "graphs.junk"
#if (not os.access(graphdir, os.F_OK)):
#    os.mkdir(graphdir)
#outputDirFile  = file('./outputDir.junk','w');  outputDirFile.write(WNS.outputDir); outputDirFile.close()
### postprocessing is specified in systemTest.py

