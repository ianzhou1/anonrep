import pprint
import re
import sys

import config
from util import Constants, send, sendrecv, powm, modinv, sighash, randkey, randkeyRP

# client class
class Client:
	def __init__(self, server_host, server_port):
		# core variables
		self.pri_key = randkey()
		self.pub_key = powm(Constants.G, self.pri_key)
		self.generator = None

		# socket variables
		self.server_addr = (server_host, server_port)

		# new client
		send(self.server_addr, [Constants.NEW_CLIENT, self.pub_key])

	def sign(self, msg):
		# ElGamal signature
		k = randkeyRP(1, Constants.MOD - 2)
		r = powm(self.generator, k, Constants.MOD - 1)
		s = (sighash(msg) - self.pri_key * r) * modinv(k, Constants.MOD - 1)
		s %= (Constants.MOD - 1)

		return (r, s)

	def get_stp(self):
		return powm(self.generator, self.pri_key)

	def post(self, msg, rep):
		self.generator = sendrecv(self.server_addr, [Constants.GET_GENERATOR])

		stp = self.get_stp()
		sig = c.sign(msg)

		# TODO: Find wallets that suffice, use them.
		send(self.server_addr, [Constants.NEW_MESSAGE, msg, stp, sig])

	def vote(self, amount, msg_id):
		# TODO: verify server-side that amount is either +1 or -1
		send(self.server_addr, [Constants.NEW_FEEDBACK, msg_id, amount, c.sign('{};{}'.format(msg_id, amount))])

	def show_help(self):
		print('Instructions:')
		print('--------------------------------------------------------')
		print('HELP           : Displays this help message')
		print('SHOW           : Shows message')
		print('WRITE [rep]    : Write a message with reputation [rep]')
		print('VOTE UP [num]  : Votes up the message with ID [num]')
		print('VOTE DOWN [num]: Votes down the message with ID [num]')
		print('--------------------------------------------------------')

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('USAGE: python client.py server_host server_port')
		sys.exit(1)

	client_host = sys.argv[1]
	client_port = int(sys.argv[2])
	c = Client(client_host, client_port)
	c.show_help()

	while True:
		try:
			s = input('> ').upper()
			if s == 'HELP':
				c.show_help()
			elif s == 'SHOW':
				messages = sendrecv(config.COORDINATOR_ADDR, [Constants.DISP_BOARD])
				pprint.PrettyPrinter(indent=4).pprint(messages)
			elif re.match("WRITE \d+", s) is not None:
				msg = input('Write message here: ')
				# TODO: Compute nym
				# TODO: encrypt msg with private key
				c.post(msg, int(s.split()[-1]))
				pass
			elif re.match("VOTE UP \d+", s) is not None:
				c.vote(1, int(s.split()[-1]))
				pass
			elif re.match("VOTE DOWN \d+", s) is not None:
				c.vote(-1, int(s.split()[-1]))
				pass
			else:
				print('Invalid command. Type in HELP for instructions.')
		except KeyboardInterrupt:
			print()
			break
