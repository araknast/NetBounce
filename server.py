#!/usr/bin/env python3
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

class Pong(LineReceiver):
    def __init__(self, players):
        self.players: dict = players
        self.state: str = "REGISTER"
        self.name: str = None
    def connectionMade(self) -> None:
        self.sendLine(b"GIVE NAME")
    def lineReceived(self, line) -> None:
        if self.state == "REGISTER":
            self.register_player(line)
        elif self.state == "REGISTERED":
            self.sendLine(b"NEED MORE PLAYERS")
        else:
            self.send_coords(line)

    def connectionLost(self, reason):
        if self.name in self.players:
            del self.players[self.name]

    def register_player(self, name) -> None: # using snake_case because this is not a twisted method
        self.state = "REGISTERED"
        #self.sendLine(b"REGISTERED")
        self.name = name
        self.players[name] = self
        if len(self.players) == 2:
            self.sendLine(b"PLAYER 2")
            for name, protocol in self.players.items():
                protocol.state = "PLAY"
                protocol.sendLine(b"PLAY")
        else:
            self.sendLine(b"NEED MORE PLAYERS")

    def send_coords(self, coords):
        for name, protocol in self.players.items():
            if protocol != self:
                protocol.sendLine(coords)

class pongFactory(Factory):
    def __init__(self):
        self.players = {}
    def buildProtocol(self, addr):
        return Pong(self.players)

reactor.listenTCP(6969, pongFactory())
reactor.run()
