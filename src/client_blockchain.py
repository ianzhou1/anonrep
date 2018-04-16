import pprint
import re
import sys

import blockchain as bc
import config

from client import Client
from util import Constants, powm, send, sendrecv


class BlockchainClient(Client):
	def __init__(self, server_host, server_port):
		self.contract_address = sendrecv(config.COORDINATOR_ADDR, [Constants.GET_CONTRACT_ADDRESS])
		self.blockchain = bc.LocalBlockchain()
		self.blockchain.connect_to_contract('reputation.sol', self.contract_address)
		self.wallets = [bc.generate_keypair()]
		super().__init__(server_host, server_port)

	def post(self, msg, rep):
		generator = sendrecv(self.server_addr, [Constants.GET_GENERATOR])

		# see if wallets have enough reputation
		if sum(self.blockchain.get_balance(x.address) for x in self.wallets) < rep:
			print('Error: You do not have enough reputation to post that.')

		stp = powm(generator, self.pri_key)
		sig = c.sign(msg, generator)

		addresses = [w.address for w in self.wallets]
		signatures = [bc.sign(w, w.address).signature.hex() for w in self.wallets]

		# TODO: Have more than one wallet.
		send(self.server_addr, [Constants.NEW_MESSAGE, msg, stp, sig, addresses, signatures])

	def vote(self, amount, msg_id):
		messages = sendrecv(config.COORDINATOR_ADDR, [Constants.DISP_BOARD])

		# verify message id
		if msg_id < 0 or msg_id >= len(messages):
			self.eprint('Invalid message id.')
			return

		msg = messages[msg_id][1][Constants.MSG]
		sig = []

		send(self.server_addr, [Constants.NEW_FEEDBACK, msg_id, msg, amount, sig])

	def show_help(self):
		print('Instructions:')
		print('--------------------------------------------------------')
		print('HELP           : Displays this help message')
		print('SHOW           : Shows message')
		print('WRITE [rep]    : Write a message with reputation [rep]')
		print('VOTE UP [num]  : Votes up the message with ID [num]')
		print('VOTE DOWN [num]: Votes down the message with ID [num]')
		print('GET REP        : Displays your reputation')
		print('--------------------------------------------------------')


if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('USAGE: python client_blockchain.py server_host server_port')
		sys.exit(1)

	client_host = sys.argv[1]
	client_port = int(sys.argv[2])
	c = BlockchainClient(client_host, client_port)
	c.show_help()

	while True:
		try:
			s = input('> ').strip().upper()
			if s == 'HELP':
				c.show_help()
			elif s == 'SHOW':
				messages = sendrecv(config.COORDINATOR_ADDR, [Constants.DISP_BOARD])
				pprint.PrettyPrinter(indent=4).pprint(messages)
			elif s == 'GET REP':
				print('Your reputation is: {}'.format(
					sum(c.blockchain.get_balance(x.address) for x in c.wallets)))
			elif re.match("^WRITE \d+$", s) is not None:
				msg = input('Write message here: ')
				c.post(msg, int(s.split()[-1]))
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
