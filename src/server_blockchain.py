import sys

import blockchain as bc
import config
import lrs

from server import Server
from util import Constants, send, msg_hash
from hashlib import sha1

class BlockchainServer(Server):
	"""Server implementation for the blockchain version of AnonRep."""

	def __init__(self, host, port):
		super().__init__(host, port)
		# add items to self.respond and self.msg_types
		new_respond = {
			Constants.NEW_MESSAGE: self.new_message,
			Constants.GET_LTP_ARRAY: self.get_ltp_array
		}

		new_msg_types = {
			Constants.NEW_MESSAGE: [str, list, list, list],
			Constants.GET_LTP_ARRAY: []
		}

		assert set(new_respond.keys()) == set(new_msg_types.keys())

		self.respond.update(new_respond)
		self.msg_types.update(new_msg_types)

	def verify_lrs_signature(self, client_msg, client_sig):
		# modify copy of ltp_array to prevent duplicate voting
		ltp_array = list(self.ltp_list.keys())
		ltp_array.append(msg_hash(client_msg, sha1))

		return lrs.verify(client_msg, ltp_array, *client_sig)

	def new_message(self, msg_args):
		"""Handles posting a new message to the message board."""
		client_msg, addresses, signatures, addr = msg_args

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
			[Constants.POST_MESSAGE, client_msg, addresses, addr])

	def get_ltp_array(self, s, msg_args):
		# send long term pseudonym list
		send(s, list(self.ltp_list.keys()))


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
