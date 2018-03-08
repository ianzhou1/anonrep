import sys
from util import Constants, randkey, powm, send

# client class
class Client:
	def __init__(self, server_host, server_port):
		# core variables
		self.pri_key = randkey()
		self.pub_key = powm(Constants.G, self.pri_key)

		# socket variables
		self.server_addr = (server_host, server_port)

		# new client
		send(self.server_addr, [Constants.NEW_CLIENT, self.pub_key])

	def post(self, msg, nym, sig):
		# new message post
		msg = '{} {} {} {}'.format(Constants.NEW_MESSAGE, msg, nym, sig)
		send(self.server_addr, msg)

# TODO Make this long-running
if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('USAGE: python client.py server_host server_port')
		sys.exit(1)
	c = Client(sys.arv[1], int(sys.argv[2]))
