import sys
import socket
from util import *

# client class
class Client():
	def __init__(self, server_host, server_port):
		# core variables
		self.pri_key = randkey()
		self.pub_key = powm(Constants.G, self.pri_key)

		# socket variables
		self.server_addr = (server_host, server_port)
		self.cs = socket.socket()
		self.cs.connect(self.server_addr)

		# new client
		msg = '{} {}'.format(
				Constants.NEW_CLIENT,
				self.pub_key
		)
		send(cs, msg)

	def run():
		pass
