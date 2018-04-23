import pprint
import re
import sys

import config
import lrs
from util import Constants, send, sendrecv, powm, modinv, msg_hash, randkey, randkeyRP, eprint
from hashlib import sha1


class Client:
	"""Base implementation of client."""

	def __init__(self, server_host, server_port):
		self.name = 'CLIENT'

		# core variables
		self.pri_key = randkey()
		self.pub_key = powm(Constants.G, self.pri_key)

		# socket variables
		self.server_addr = (server_host, server_port)

		# new client
		send(self.server_addr, [Constants.NEW_CLIENT, self.pub_key])

	def sign(self, msg, generator):
		"""Sign with ElGamal signature."""
		r, s = 0, 0

		while s == 0:
			k = randkeyRP(1, Constants.P - 2)
			r = powm(generator, k)
			s = (msg_hash(msg, sha1) - self.pri_key * r) * modinv(k, Constants.P - 1)
			s %= Constants.P - 1

		return (r, s)

	def post(self, msg):
		"""Post a message."""
		generator = sendrecv(self.server_addr, [Constants.GET_GENERATOR])

		stp = powm(generator, self.pri_key)
		sig = self.sign(msg, generator)

		send(self.server_addr, [Constants.NEW_MESSAGE, msg, stp, sig])

	def vote(self, amount, msg_id):
		"""Vote on a message."""
		messages = sendrecv(config.COORDINATOR_ADDR, [Constants.DISP_BOARD])

		# verify message id
		if msg_id < 0 or msg_id >= len(messages):
			eprint(self.name, 'Invalid message id.')
			return

		msg = messages[msg_id][1][Constants.MSG]
		generator = sendrecv(self.server_addr, [Constants.GET_GENERATOR])
		stp_array = sendrecv(self.server_addr, [Constants.GET_STP_ARRAY])
		stp = powm(generator, self.pri_key)
		stp_idx = stp_array.index(stp)

		# modify stp_array to prevent duplicate voting
		stp_array.append(msg_hash(msg, sha1))

		sig = lrs.sign(msg, self.pri_key, stp_idx, stp_array, g=generator)

		send(self.server_addr, [Constants.NEW_FEEDBACK, msg_id, msg, amount, sig])

	def get_message_board(self):
		return sendrecv(config.COORDINATOR_ADDR, [Constants.DISP_BOARD])

	def show(self):
		"""Display the message board."""
		messages = self.get_message_board()

		# modify for printing purposes
		for msg_id, msg_info in messages:
			msg_info[Constants.NYM] %= Constants.MOD
		pprint.PrettyPrinter(indent=4).pprint(messages)

	def show_help(self):
		"""Display help text."""
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

	client_host = sys.argv[1]
	client_port = int(sys.argv[2])
	c = Client(client_host, client_port)
	c.show_help()

	while True:
		try:
			s = input('> ').strip().upper()
			if s == 'HELP':
				c.show_help()
			elif s == 'SHOW':
				c.show()
			elif re.match("^WRITE$", s) is not None:
				msg = input('Write message here: ')
				c.post(msg)
				pass
			elif re.match("^VOTE UP \d+$", s) is not None:
				c.vote(1, int(s.split()[-1]))
				pass
			elif re.match("^VOTE DOWN \d+$", s) is not None:
				c.vote(-1, int(s.split()[-1]))
				pass
			else:
				print('Invalid command. Type in HELP for instructions.')
		except KeyboardInterrupt:
			print()
			break
