import random
import sys
import time
from threading import Thread

import blockchain as bc
import config

from board_blockchain import BlockchainMessageBoard
from coordinator import Coordinator
from util import Constants, send

class BlockchainCoordinator(Coordinator):
	"""Coordinator implementation for the blockchain version of AnonRep."""

	def __init__(self, host, port):
		self.blockchain = bc.LocalBlockchain()
		self.contract_address = self.blockchain.deploy_contract('reputation.sol')
		super().__init__(host, port)

		self.board = BlockchainMessageBoard(self)

		# add items to self.respond and self.msg_types
		new_respond = {
			Constants.GET_CONTRACT_ADDRESS: self.get_contract_address
		}

		new_msg_types = {
			Constants.GET_CONTRACT_ADDRESS: []
		}

		assert set(new_respond.keys()) == set(new_msg_types.keys())

		self.respond.update(new_respond)
		self.msg_types.update(new_msg_types)

	def get_contract_address(self, s, msg_args):
		"""Handles request for reputation contract address."""
		send(s, self.contract_address)

	def update_servers(self):
		# update servers and neighbors
		random.shuffle(self.servers)
		self.servers_ready = 0
		self.broadcast_neighbors()
		# pause before beginning message phase
		while self.servers_ready != self.num_servers:
			time.sleep(0.01)

	def begin_message_phase(self):
		"""Begins message phase."""
		super().end_announcement_phase(None)

		# denotes where the message board should start looking from when calculating
		# net feedback
		self.board.message_marker = len(self.board.board)
		# reset addrs
		self.board.addrs = {}


if __name__ == '__main__':
	if len(sys.argv) != 1:
		print('USAGE: python coordinator.py')
		sys.exit(1)

	print('*** Press [ENTER] to begin message phase. ***')
	c = BlockchainCoordinator(*config.COORDINATOR_ADDR)
	try:
		thread = Thread(target=c.run)
		thread.start()

		# wait to press enter
		input()
		c.update_servers()

		while True:
			# message phase
			c.begin_message_phase()
			time.sleep(config.MESSAGE_PHASE_LENGTH_IN_SECS)

			# feedback phase
			c.begin_feedback_phase()
			time.sleep(config.FEEDBACK_PHASE_LENGTH_IN_SECS)

			# coinshuffle phase
			c.board.start_coinshuffle()
			while c.phase != Constants.COINSHUFFLE_FINISHED_PHASE:
				time.sleep(0.1)
	finally:
		c.ss.close()
