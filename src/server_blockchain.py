import sys

import blockchain as bc
import config

from server import Server
from util import Constants, send

class BlockchainServer(Server):
	"""Server implementation for the blockchain version of AnonRep."""

	def __init__(self, host, port):
		super().__init__(host, port)
		# add items to self.respond and self.msg_types
		new_respond = {
			Constants.NEW_MESSAGE: self.new_message
		}

		new_msg_types = {
			Constants.NEW_MESSAGE: [str, int, list, list, list, list]
		}

		assert set(new_respond.keys()) == set(new_msg_types.keys())

		self.respond.update(new_respond)
		self.msg_types.update(new_msg_types)

	def new_message(self, msg_args):
		"""Handles posting a new message to the message board."""
		client_msg, client_stp, client_sig, addresses, signatures, addr = msg_args

		# verify message, pseudonym, and signature
		if not self.verify_signature(client_msg, client_stp, client_sig):
			self.eprint('Message signature verification failed.')
			return

		if len(addresses) != len(signatures) or len(addresses) == 0:
			self.eprint('Invalid number of addresses/signatures.')
			return

		# verify wallets
		for (address, signature) in zip(addresses, signatures):
			if not bc.verify(address, address, signature):
				self.eprint('Signature verification failed.')
				return

		# pass on to coordinator
		send(config.COORDINATOR_ADDR,
			[Constants.POST_MESSAGE, client_msg, client_stp, addresses, addr])


if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('USAGE: python server_blockchain.py host port')
		sys.exit(1)

	server_host = sys.argv[1]
	server_port = int(sys.argv[2])
	s = BlockchainServer(server_host, server_port)

	try:
		s.run()
	finally:
		s.ss.close()
