# Constanze over TCP/IP
import openwns
import openwns.logger
import openwns.distribution

import constanze.traffic
from constanze.node import ConstanzeComponent, Listener, TCPBinding, TCPListenerBinding
import constanze.evaluation.default

import tcp
import tcp.TCP

import ip
from ip.BackboneHelpers import Station_10BaseT 
from ip.VirtualARP import VirtualARPServer
from ip.VirtualDNS import VirtualDNSServer
from ip.VirtualDHCP import VirtualDHCPServer

import glue.support.Configuration

import copper.Copper

# create an instance of the WNS configuration
# The variable must be called WNS!!!!
WNS = openwns.Simulator(simulationModel = openwns.node.NodeSimulationModel())
WNS.outputStrategy = openwns.simulator.OutputStrategy.DELETE

wire = copper.Copper.Wire("theWire")

client = Station_10BaseT(name = "client",
                         _wire = wire,
                         _domainName = "Host4",
                         _defaultRouter = "127.0.0.1")

server = Station_10BaseT(name = "server",
                         _wire = wire,
                         _domainName = "Host3",
                         _defaultRouter = "127.0.0.1")

serverIP = server.ip.domainName
clientIP = client.ip.domainName

clientTCP = tcp.TCP.TCPComponent(client, "tcp", client.ip.dataTransmission, client.ip.notification)
serverTCP = tcp.TCP.TCPComponent(server, "tcp", server.ip.dataTransmission, server.ip.notification)

speed = 10E6 # 10BaseT = 10MBit/s
# Traffic load
meanPacketSize = 500 * 8 # bits
loadFactor = 0.1 # rho = 10%
throughputPerStation = speed * loadFactor
startTime = 1.0 # [s]
duration = 10.0
# The TCP connection is opened at t=01s and closed at t=31s.

#logger = WNS.nodes[0].logger
logger = client.logger
traffic = constanze.traffic.CBR0(startTime, throughputPerStation, meanPacketSize, duration=duration, parentLogger=logger)

tcpClientBinding = TCPBinding(clientIP, serverIP, 1024) # connection to server
constanzeClient = ConstanzeComponent(client, "192.168.0.4.constanze")
constanzeClient.addTraffic(tcpClientBinding, traffic)

tcpServerListenerBinding = TCPListenerBinding(1024)
serverListener = Listener(str(serverIP)+".listener")
constanzeServer = ConstanzeComponent(server, "192.168.0.3.constanze")
constanzeServer.addListener(tcpServerListenerBinding, serverListener)

WNS.simulationModel.nodes.append(client)
WNS.simulationModel.nodes.append(server)

# one Virtual ARP Zone
varp = VirtualARPServer("vARP", "theWire")
WNS.simulationModel.nodes = [varp] + WNS.simulationModel.nodes

vdhcp = VirtualDHCPServer("vDHCP@",
                          "theWire",
                          "192.168.0.2", "192.168.254.253",
                          "255.255.0.0")

vdns = VirtualDNSServer("vDNS", "ip.DEFAULT.GLOBAL")
WNS.simulationModel.nodes.append(vdns)

WNS.simulationModel.nodes.append(vdhcp)

WNS.maxSimTime = 12.0

client.components[1].bottleNeckDetective.config.logger.enabled = False
server.components[1].bottleNeckDetective.config.logger.enabled = False
glue.support.Configuration.ShortCut.loggerEnabled = False

WNS.modules.glue.logger.enabled = False

constanze.evaluation.default.installEvaluation(WNS,
                                               maxPacketDelay = 0.0001,
                                               maxPacketSize = 16000,
                                               maxBitThroughput = 2* throughputPerStation,
                                               maxPacketThroughput = 2 * throughputPerStation/meanPacketSize,
                                               delayResolution = 1000,
                                               sizeResolution = 2000,
                                               throughputResolution = 10000)

openwns.setSimulator(WNS)