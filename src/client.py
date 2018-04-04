import pprint
import re
import sys

import config
from util import Constants, deserialize, powm, randkey, send, sendrecv

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

	def encrypt(self, msg):
		# TODO: encrypt msg with private key and return encrypted msg
		return msg

	def get_nym(self):
		# TODO: get nym and return it
		return self.pub_key

	def post(self, msg, nym, sig):
		# new message post
		send(self.server_addr, [Constants.NEW_MESSAGE, msg, nym, sig])

def show_help():
	print('Instructions:')
	print('--------------------------------------------------------')
	print('HELP           : Displays this help message')
	print('SHOW           : Shows message')
	print('WRITE          : Write a message')
	print('VOTE UP [num]  : Votes up the message with ID [num]')
	print('VOTE DOWN [num]: Votes down the message with ID [num]')
	print('--------------------------------------------------------')

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('USAGE: python client.py server_host server_port')
		sys.exit(1)
	c = Client(sys.argv[1], int(sys.argv[2]))
	show_help()
	while True:
		try:
			s = input('> ').upper()
			if s == 'HELP':
				show_help()
			elif s == 'SHOW':
				messages = deserialize(sendrecv(config.COORDINATOR_ADDR, [Constants.DISP_BOARD]))
				pprint.PrettyPrinter(indent=4).pprint(messages)
			elif s == 'WRITE':
				msg = input('Write message here: ')
				# TODO: Compute nym
				# TODO: encrypt msg with private key
				c.post(c.encrypt(msg), c.get_nym(), c.pub_key)
				pass
			elif re.match("VOTE UP \d+", s) is not None:
				# TODO
				print('vote up...')
				pass
			elif re.match("VOTE DOWN \d+", s) is not None:
				# TODO
				print('vote down...')
				pass
			else:
				print('Invalid command. Type in HELP for instructions.')
		except KeyboardInterrupt:
			print()
			break
