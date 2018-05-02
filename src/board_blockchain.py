from collections import defaultdict

from board import MessageBoard
from util import Constants, send, sendbytes, sendrecv, eprint

class BlockchainMessageBoard(MessageBoard):
	"""Message board that stores reputation on the blockchain."""

	def __init__(self, coordinator):
		super().__init__(coordinator)

		self.reps = {}
		self.msg_id_to_addr = {}
		self.used_wallets = set()

		# add items to self.respond and self.msg_types
		new_respond = {
			Constants.POST_MESSAGE: self.post_message,
			Constants.SHUFFLE: self.end_coinshuffle,
		}

		new_msg_types = {
			Constants.POST_MESSAGE: [str, list, list],
			Constants.SHUFFLE: [list],
		}

		assert set(new_respond.keys()) == set(new_msg_types.keys())

		self.respond.update(new_respond)
		self.msg_types.update(new_msg_types)

		# for convenience
		self.blockchain = self.coordinator.blockchain

	def post_message(self, msg_args):
		"""Posts message to board and increment message id."""
		client_msg, addresses, sender_addr = msg_args

		# verify that there is either one address with 0 reputation or all addresses
		# have 1 reputation, and that the addresses have never been used before.
		if len(addresses) > 1:
			for addr in addresses:
				if self.blockchain.get_reputation(addr) != 1:
					eprint(self.name, 'All wallets should have had >0 reputation.')
					return
				if addr in self.used_wallets:
					eprint(self.name, '{} has already been used in a post'.format(addr))

		self.used_wallets.update(addresses)

		self.reps[tuple(sender_addr)] = 0
		self.msg_id_to_addr[self.msg_id] = tuple(sender_addr)

		# post message to board and increment message id
		self.board.append([self.msg_id, {
				Constants.MSG: client_msg,
				Constants.REP: addresses,
				Constants.FB: Constants.INIT_FEEDBACK
		}])

		self.msg_id += 1

	def start_coinshuffle(self):
		"""Begins Coinshuffle phase."""
		# Commits all the changes in reputation to the blockchain.
		promises = []
		for i in range(self.message_marker, len(self.board)):
			addresses = self.board[i][1][Constants.REP]
			net_fb = (self.board[i][1][Constants.FB][0] +
				self.board[i][1][Constants.FB][1])
			if net_fb > 0:
				promises.append(self.blockchain.add_reputation(addresses[0], net_fb))
			elif net_fb < 0:
				to_remove = -net_fb
				for address in addresses:
					can_remove = min(to_remove, self.blockchain.get_reputation(address))
					promises.append(
						self.blockchain.remove_reputation(address, can_remove))
					to_remove -= can_remove
					if to_remove <= 0:
						break

		for promise in promises:
			promise.resolve()

		# reset used_wallets
		self.used_wallets = set()

		self.coordinator.phase = Constants.COINSHUFFLE_PHASE
		# contains a list of (wallet, balance_of_wallet) that need to be transfered
		# to another wallet
		self.spending_wallets = []
		self.spending_wallets_total = 0

		# determine which clients should participate in the coinshuffle
		final_balances = defaultdict(int)
		for i in range(self.message_marker, len(self.board)):
			addr = self.msg_id_to_addr[i]

			# check if this user has > 0 reputation
			for wallet in self.board[i][1][Constants.REP]:
				balance = self.blockchain.get_reputation(wallet)
				final_balances[addr] += balance
				if balance > 0:
					self.spending_wallets.append((wallet, balance))
					self.spending_wallets_total += balance

		# let all clients know whether they are participating in the shuffle or not.
		participants = []
		for addr, balance in final_balances.items():
			if balance > 0:
				encryption_key = sendrecv(
					addr, [Constants.PARTICIPATION_STATUS, balance])
				participants.append((addr, encryption_key))
			else:
				send(addr, [Constants.PARTICIPATION_STATUS, balance])

		# iterate over participants and send them the encyption keys that
		# they need, get ack.
		e_keys = []
		for i, (addr, e_key) in enumerate(reversed(participants)):
			if i == 0:
				next_addr = self.coordinator.addr
			else:
				next_addr = participants[len(participants) - i][0]
			# send participants encryption keys next hop in the ring
			sendrecv(addr, [Constants.KEYS, next_addr, e_keys])
			e_keys.append(e_key)

		# start the shuffling
		if len(participants) == 0:
			self.coordinator.phase = Constants.COINSHUFFLE_FINISHED_PHASE
			return
		sendbytes(participants[0][0], b'')

	def end_coinshuffle(self, msg_args):
		"""Transfer reputation to the shuffled list of new wallets."""
		addrs, = msg_args

		assert(self.spending_wallets_total == len(addrs))
		promises = []
		cur = 0
		for wallet, balance in self.spending_wallets:
			for i in range(balance):
				promises.append(
					self.coordinator.blockchain.transfer(wallet, addrs[cur]))
				cur += 1

		# wait for all transfers to be mined.
		for promise in promises:
			promise.resolve()

		self.coordinator.phase = Constants.COINSHUFFLE_FINISHED_PHASE
