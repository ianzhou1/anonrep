from util import Constants, send, sprint, eprint


class MessageBoard:
	"""Base message board class."""

	def __init__(self, coordinator):
		self.name = 'BOARD'
		self.coordinator = coordinator

		# core variables
		self.board = [] # list of (message, pseudonym, reputation score)
		self.msg_id = 0

		# respond dict for received messages
		self.respond = {
				Constants.POST_MESSAGE:	self.post_message,
				Constants.POST_FEEDBACK: self.post_feedback,
				Constants.DISP_BOARD: self.disp_board,
				Constants.RESTART_ROUND: self.restart_round,
		}

		# message type dict for received messages
		self.msg_types = {
				Constants.POST_MESSAGE: [str, int, int],
				Constants.POST_FEEDBACK: [int, int],
				Constants.DISP_BOARD: [],
				Constants.RESTART_ROUND: [],
		}

	def verify_message(self, msg, phase):
		"""Verifies that the incoming message is valid."""
		if len(msg) == 0:
			return False

		msg_head, *msg_args = msg

		# verify that msg_head is in respond dict
		ret = (msg_head in self.respond)

		# verify that
		if ((msg_head == Constants.POST_FEEDBACK and
					phase == Constants.MESSAGE_PHASE) or
				(msg_head == Constants.POST_MESSAGE and
					phase == Constants.FEEDBACK_PHASE)):
			return False

		# verify that msg_args length matches expected
		ret = ret and (len(msg_args) == len(self.msg_types[msg_head]))

		# verify that all arguments are of the appropriate type
		for i in range(len(msg_args)):
			ret = ret and isinstance(msg_args[i], self.msg_types[msg_head][i])

		return ret

	def post_message(self, msg_args):
		"""Handles message post. Posts message to board and increment message id."""
		client_msg, client_stp, client_score = msg_args

		self.board.append([self.msg_id, {
				Constants.MSG: client_msg,
				Constants.NYM: client_stp,
				Constants.REP: client_score,
				Constants.FB: Constants.INIT_FEEDBACK
		}])

		self.msg_id += 1

	def post_feedback(self, msg_args):
		"""Handles vote. Verifies vote and posts it to the message board."""
		client_msg_id, client_vote = msg_args

		# verify client message id
		if client_msg_id < 0 or client_msg_id >= len(self.board):
			eprint(self.name, 'Invalid message id.')
			return

		# post feedback to board
		client_fb = self.board[client_msg_id][1][Constants.FB]
		if client_vote >= 0:
			client_fb = (client_fb[0] + client_vote, client_fb[1])
		else:
			client_fb = (client_fb[0], client_fb[1] + client_vote)
		self.board[client_msg_id][1][Constants.FB] = client_fb

	def disp_board(self, s, msg_args):
		"""Handles request for message board."""
		send(s, self.board)

	def restart_round(self, msg_args):
		"""Handles signal to restart the round."""
		sprint(self.name, 'Round has ended. Starting new round...')
		self.coordinator.phase = Constants.ANNOUNCEMENT_PHASE

	def process_message(self, s, msg, phase):
		"""Verifies and responds to message."""
		if not self.verify_message(msg, phase):
			eprint(self.name, 'Error processing ' + str(msg) + '.')
			s.close()
			return

		msg_head, *msg_args = msg

		# respond to received message
		if msg_head in Constants.OPEN_SOCKET:
			self.respond[msg_head](s, msg_args)
		else:
			self.respond[msg_head](msg_args)
		s.close()
