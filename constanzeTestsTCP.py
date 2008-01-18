# Constanze over TCP/IP
import wns.WNS
import wns.Distribution
import ip

#from constanze.Constanze import Constanze, Poisson, CBR
import constanze.Constanze
from constanze.Node import ConstanzeComponent, Listener, TCPBinding, TCPListenerBinding
from ip.BackboneHelpers import Router_10BaseT, Station_10BaseT 
from ip.IP import IP
import copper.Copper
import glue
import glue.support.Configuration
import tcp.TCP

# create an instance of the WNS configuration
# The variable must be called WNS!!!!
WNS = wns.WNS.WNS()
WNS.outputStrategy = wns.WNS.OutputStrategy.DELETE

wire = copper.Copper.Wire("theWire")

client = Station_10BaseT(name = "client",
                         _wire = wire,
                         _ipAddress = "192.168.0.4",
                         _defaultRouter = "127.0.0.1")

server = Station_10BaseT(name = "server",
                         _wire = wire,
                         _ipAddress = "192.168.0.3",
                         _defaultRouter = "127.0.0.1")

serverIP = server.ip.address

clientTCP = tcp.TCP.TCPComponent(client, "tcp", client.ip.dataTransmission, client.ip.notification)
serverTCP = tcp.TCP.TCPComponent(server, "tcp", server.ip.dataTransmission, server.ip.notification)

speed = 10E6 # 10BaseT = 10MBit/s
# Traffic load
meanPacketSize = 500 * 8 # bits
loadFactor = 0.1 # rho = 10%
throughputPerStation = speed * loadFactor
startTime = 1.0 # [s]
duration = 30.0
# The TCP connection is opened at t=01s and closed at t=31s.

#logger = WNS.nodes[0].logger
logger = client.logger
traffic = constanze.Constanze.CBR0(startTime, throughputPerStation, meanPacketSize, duration=duration, parentLogger=logger)

tcpClientBinding = TCPBinding(serverIP, 1024) # connection to server
constanzeClient = ConstanzeComponent(client, "192.168.0.4.constanze")
constanzeClient.addTraffic(tcpClientBinding, traffic)

tcpServerListenerBinding = TCPListenerBinding(1024)
serverListener = Listener(str(serverIP)+".listener")
constanzeServer = ConstanzeComponent(server, "192.168.0.3.constanze")
constanzeServer.addListener(tcpServerListenerBinding, serverListener)


# Scenario Setup is now complete
# We still need to build the neighbour caches
ip.buildNeighbourCaches()

WNS.nodes.append(client)
WNS.nodes.append(server)

#WNS.maxSimTime = 1000.0
WNS.maxSimTime = 50.0

#wns.Logger.globalRegistry.enableLoggers("GLUE", False)
#client.Glue.loggerEnabled = False
#server.Glue.loggerEnabled = False
client.components[1].bottleNeckDetective.config.logger.enabled = False
server.components[1].bottleNeckDetective.config.logger.enabled = False
glue.support.Configuration.ShortCut.loggerEnabled = False
#glue.support.Configuration.BottleNeckDetective.loggerEnabled = False
WNS.modules.glue.logger.enabled = False
