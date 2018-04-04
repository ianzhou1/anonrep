import sys

from util import Constants, serialize, send

# message board class
class MessageBoard:
	def __init__(self, coordinator):
		self.coordinator = coordinator

		# core variables
		self.board = {} # message id and (message, pseudonym, reputation score)
		self.msg_id = 0

		# respond dict for received messages
		self.respond = {
				Constants.POST_MESSAGE:	self.post_message,
				Constants.POST_FEEDBACK: self.post_feedback,
				Constants.DISP_BOARD: self.disp_board,
				Constants.END_MESSAGE_PHASE: self.end_message_phase
		}

		# message length dict for received messages
		self.msg_lens = {
				Constants.POST_MESSAGE: 3,
				Constants.POST_FEEDBACK: 2,
				Constants.DISP_BOARD: 0,
				Constants.END_MESSAGE_PHASE: 1
		}

	def verify_message(self, msg, phase):
		if len(msg) == 0:
			return False

		msg_head, *msg_args = msg

		# verify that msg_head is in respond dict
		ret = (msg_head in self.respond)

		# verify that
		if ((msg_head == Constants.POST_FEEDBACK and phase == Constants.MESSAGE_PHASE) or
				(msg_head == Constants.POST_MESSAGE and phase == Constants.FEEDBACK_PHASE)):
			return False

		# verify that msg_args length matches expected
		ret = ret or (len(msg_args) == self.msg_lens[msg_head])

		# verify that all arguments are of the appropriate type
		try:
			if msg_head == Constants.POST_MESSAGE:
				client_stp, client_rep = [int(_) for _ in msg_args[1:]]
			else:
				msg_args = [int(_) for _ in msg_args]
		except ValueError:
			ret = False

		return ret

	def post_message(self, msg_head, msg_args):
		client_msg, client_stp, client_rep = msg_args
		client_stp = int(client_stp)
		client_rep = int(client_rep)

		# post message to board and increment message id
		self.board[self.msg_id] = {
				Constants.MSG: client_msg,
				Constants.NYM: client_stp,
				Constants.REP: client_rep,
				Constants.FB: Constants.INIT_FEEDBACK
		}
		self.msg_id += 1

	def post_feedback(self, msg_head, msg_args):
		client_msg_id, client_vote = [int(_) for _ in msg_args]

		# [TODO] verify client message id
		# post feedback to board
		client_fb = self.board[client_msg_id][Constants.FB]
		if client_vote >= 0:
			client_fb = (client_fb[0] + client_vote, client_fb[1])
		else:
			client_fb = (client_fb[0], client_fb[1] + client_vote)
		self.board[self.msg_id][Constants.FB] = client_fb

	def disp_board(self, s, msg_head, msg_args):
		# send message board
		msg = serialize(self.board)
		send(s, msg)

	def end_message_phase(self, msg_head, msg_args):
		self.eprint('Round has ended. Starting new round...')
		self.coordinator.phase = Constants.ANNOUNCEMENT_PHASE

	def process_message(self, s, msg, phase):
		# verify message information
		if not self.verify_message(msg, phase):
			self.eprint('Error processing message.')
			s.close()
			return

		msg_head, *msg_args = msg

		# respond to received message
		if msg_head in Constants.OPEN_SOCKET:
			self.respond[msg_head](s, msg_head, msg_args)
		else:
			self.respond[msg_head](msg_head, msg_args)
		s.close()

	def eprint(self, err):
		print('[BOARD] ' + err, file=sys.stderr)
