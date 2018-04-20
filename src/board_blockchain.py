from collections import defaultdict

import blockchain as bc
from board import MessageBoard
from util import Constants, send, sendbytes, sendrecv

class BlockchainMessageBoard(MessageBoard):
	def __init__(self, coordinator):
		super().__init__(coordinator)

		self.addrs = {}

		# add items to self.respond and self.msg_types
		new_respond = {
			Constants.POST_MESSAGE: self.post_message,
			Constants.SHUFFLE: self.end_coinshuffle,
		}

		new_msg_types = {
			Constants.POST_MESSAGE: [str, int, list, list],
			Constants.SHUFFLE: [list],
		}

		assert set(new_respond.keys()) == set(new_msg_types.keys())

		self.respond.update(new_respond)
		self.msg_types.update(new_msg_types)

		# for convenience
		self.blockchain = self.coordinator.blockchain

	def begin_message_phase(self):
		# denotes where the message board should start looking from when calculating votes
		self.message_marker = len(self.board)
		# reset addrs
		self.addrs = {}

	def end_feedback_phase(self):
		self.coordinator.phase = Constants.VOTE_CALCULATION_PHASE

		for i in range(self.message_marker, len(self.board)):
			addresses = self.board[i][1][Constants.REP]
			net_fb = self.board[i][1][Constants.FB][0] + self.board[i][1][Constants.FB][1]
			if net_fb > 0:
				self.blockchain.add_reputation(addresses[0], net_fb)
			elif net_fb < 0:
				to_remove = -net_fb
				for address in addresses:
					can_remove = min(to_remove, self.blockchain.get_balance(address))
					self.blockchain.remove_reputation(address, can_remove)
					to_remove -= can_remove
					if to_remove <= 0:
						break

	def post_message(self, msg_args):
		client_msg, client_stp, addresses, addr = msg_args

		self.addrs[client_stp] = tuple(addr)

		# post message to board and increment message id
		self.board.append([self.msg_id, {
				Constants.MSG: client_msg,
				Constants.NYM: client_stp,
				Constants.REP: addresses,
				Constants.FB: Constants.INIT_FEEDBACK
		}])

		self.msg_id += 1

	def post_feedback(self, msg_args):
		client_msg_id, client_vote = msg_args

		# verify client message id
		if client_msg_id < 0 or client_msg_id >= len(self.board):
			self.eprint('Invalid message id.')
			return

		# post feedback to board and blockchain
		client_fb = self.board[client_msg_id][1][Constants.FB]
		if client_vote >= 0:
			client_fb = (client_fb[0] + client_vote, client_fb[1])

		else:
			client_fb = (client_fb[0], client_fb[1] + client_vote)
		self.board[client_msg_id][1][Constants.FB] = client_fb

	def start_coinshuffle(self):
		self.coordinator.phase = Constants.COINSHUFFLE_PHASE
		# contains a list of (wallet, balance_of_wallet) that need to be transfered to another wallet
		self.spending_wallets = []
		self.spending_wallets_total = 0

		# determine which clients should participate in the coinshuffle
		final_balances = defaultdict(int)
		for i in range(self.message_marker, len(self.board)):
			stp = self.board[i][1][Constants.NYM]

			# check if this user has > 0 reputation
			for wallet in self.board[i][1][Constants.REP]:
				balance = self.blockchain.get_balance(wallet)
				final_balances[stp] += balance
				if balance > 0:
					self.spending_wallets.append((wallet, balance))
					self.spending_wallets_total += balance

		participants = []
		for stp, balance in final_balances.items():
			if balance > 0:
				encryption_key, signing_key = sendrecv(
					self.addrs[stp], [Constants.PARTICIPATION_STATUS, balance])
				participants.append((self.addrs[stp], encryption_key, signing_key))
			else:
				send(self.addrs[stp], [Constants.PARTICIPATION_STATUS, balance])

		# iterate over participants and send them the encyption/signing keys that they need, get ack
		# send participants encrpytion keys, signing key
		e_keys = []
		for i, (addr, e_key, s_key) in enumerate(reversed(participants)):
			prev_s_key = participants[len(participants) - 2 - i][2]
			if i == len(participants) - 1:
				prev_s_key = ''
			if i == 0:
				next_addr = self.coordinator.addr
			else:
				next_addr = participants[len(participants) - i][0]
			sendrecv(addr, [Constants.KEYS, next_addr, e_keys, prev_s_key])
			e_keys.append(e_key)

		# start the shuffling
		sendbytes(participants[0][0], b'')

	def end_coinshuffle(self, msg_args):
		addrs, = msg_args

		# TODO move reputation from spending wallets to addrs
		assert(self.spending_wallets_total == len(addrs))
		cur = 0
		for wallet, balance in self.spending_wallets:
			for i in range(balance):
				self.coordinator.blockchain.transfer(wallet, addrs[cur])
				cur += 1

		# TODO wait for all transactions to go through before ending
		self.coordinator.phase = Constants.COINSHUFFLE_FINISHED_PHASE
