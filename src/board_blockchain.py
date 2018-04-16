from board import MessageBoard
from util import Constants

class BlockchainMessageBoard(MessageBoard):
	def __init__(self, coordinator):
		super().__init__(coordinator)

		# add items to self.respond and self.msg_types
		new_respond = {
			Constants.POST_MESSAGE: self.post_message
		}

		new_msg_types = {
			Constants.POST_MESSAGE: [str, int, list]
		}

		assert set(new_respond.keys()) == set(new_msg_types.keys())

		self.respond.update(new_respond)
		self.msg_types.update(new_msg_types)

		# for convenience
		self.blockchain = self.coordinator.blockchain

	def begin_message_phase(self):
		# denotes where the message board should start looking from when calculating votes
		self.message_marker = len(self.board)

	def end_feedback_phase(self):
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
		client_msg, client_stp, addresses = msg_args

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
