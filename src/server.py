import socket
import sys
import traceback

import config
from util import Constants, randkey, powm, serialize, deserialize, send, recv

# server class
class Server:
	def __init__(self, host, port, server_id):
		# identification
		self.server_id = server_id

		# core variables
		self.pri_key = randkey()
		self.pub_key = powm(Constants.G, self.pri_key)
		self.ltp_list = {} # long-term pseudonyms and encrypted reputation scores
		self.stp_list = {} # short-term pseudonyms and decrypted reputation scores

		# socket variables
		self.addr = (host, port)
		self.ss = socket.socket()
		self.ss.bind(self.addr)
		self.ss.listen(5)

		send(config.COORDINATOR_ADDR, [Constants.NEW_SERVER, host, port, server_id])

		# respond dict for received messages
		self.respond = {
				Constants.NEW_CLIENT: self.new_client,
				Constants.NEW_REPUTATION: self.new_reputation,
				Constants.ADD_REPUTATION: self.add_reputation,
				Constants.NEW_ANNOUNCEMENT: self.new_announcement,
				Constants.REPLACE_STP: self.replace_stp,
				Constants.NEW_MESSAGE: self.new_message,
				Constants.NEW_FEEDBACK: self.new_feedback,
				Constants.REV_ANNOUNCEMENT: self.rev_announcement,
				Constants.REPLACE_LTP: self.replace_ltp,
				Constants.UPDATE_NEIGHBORS: self.update_neighbors,
				Constants.UPDATE_NEXT_SERVER: self.update_next_server,
				Constants.UPDATE_PREV_SERVER: self.update_prev_server,
		}

		# message length dict for received messages
		self.msg_lens = {
				Constants.NEW_CLIENT: 1,
				Constants.NEW_REPUTATION: 3,
				Constants.ADD_REPUTATION: 2,
				Constants.NEW_ANNOUNCEMENT: 2,
				Constants.REPLACE_STP: 2,
				Constants.NEW_MESSAGE: 3,
				Constants.NEW_FEEDBACK: 3,
				Constants.REV_ANNOUNCEMENT: 2,
				Constants.REPLACE_LTP: 2,
				Constants.UPDATE_NEIGHBORS: 4,
				Constants.UPDATE_NEXT_SERVER: 2,
				Constants.UPDATE_PREV_SERVER: 2
		}

		assert set(self.respond.keys()) == set(self.msg_lens.keys())

	def sprint(self, s):
		print('[SERVER] ' + s)

	def eprint(self, err):
		print('[SERVER] ' + err, file=sys.stderr)

	def set_next_server(self, next_host, next_port):
		self.next_addr = (next_host, next_port)

	def set_prev_server(self, prev_host, prev_port):
		self.prev_addr = (prev_host, prev_port)

	def set_board(self, board_host, board_port):
		self.board_addr = (board_host, board_port)

	def encrypt(self, text):
		# [TODO] replace with ElGamal
		return text

	def decrypt(self, text):
		# [TODO] replace with ElGamal
		return text

	def announcement_fwd(self, ann_list):
		self.eph_key = randkey()

		# [TODO] replace with forward encrypt/decrypt
		ret = ann_list
		return ret

	def announcement_bwd(self, ann_list):
		# [TODO] replace with backward encrypt/decrypt
		ret = ann_list
		return ret

	def verifiable_shuffle(self, ann_list):
		# [TODO] replace with verifiable shuffle
		return ann_list

	def verify_message(self, msg):
		if len(msg) < 2:
			return False

		msg_head, *msg_args = msg

		# verify that msg_head is in respond dict
		ret = (msg_head in self.respond)

		# verify that msg_args length matches expected
		ret = ret or (len(msg_args) == self.msg_lens[msg_head])

		# verify that all arguments are of the appropriate type
		try:
			if msg_head == Constants.UPDATE_NEIGHBORS:
				ports = int(msg_args[1]), int(msg_args[3])
			elif msg_head == Constants.UPDATE_NEXT_SERVER or msg_head == Constants.UPDATE_PREV_SERVER:
				port = int(msg_args[1])
			elif msg_head in [Constants.NEW_ANNOUNCEMENT, Constants.REPLACE_STP]:
				ann_list = deserialize(msg_args[0])
				init_id = int(msg_args[1])
			else:
				msg_args = [int(_) for _ in msg_args]
		except ValueError:
			ret = False

		return ret

	def new_client(self, msg_head, msg_args):
		client_ltp = int(msg_args[0])
		client_rep = Constants.INIT_REPUTATION

		# initiate new reputation
		rep_args = [client_ltp, client_rep, Constants.INIT_ID]
		self.new_reputation(Constants.NEW_REPUTATION, rep_args)

	def new_reputation(self, msg_head, msg_args):
		client_ltp, client_rep, init_id = [int(_) for _ in msg_args]

		if init_id != self.server_id:
			if init_id == Constants.INIT_ID:
				init_id = self.server_id

			# encrypt client reputation
			client_rep = self.encrypt(client_rep)

			# pass reputation to next server
			send(self.next_addr, [Constants.NEW_REPUTATION, client_ltp, client_rep, init_id])
		else:
			# initiate add reputation
			rep_args = [client_ltp, client_rep]
			self.add_reputation(Constants.ADD_REPUTATION, rep_args)

	def add_reputation(self, msg_head, msg_args):
		client_ltp, client_rep = [int(_) for _ in msg_args]
		if client_ltp in self.ltp_list:
			return

		# add reputation to current server and update next server
		self.ltp_list[client_ltp] = client_rep
		send(self.next_addr, [Constants.ADD_REPUTATION, client_ltp, client_rep])

	def new_announcement(self, msg_head, msg_args):
		ann_list, init_id = msg_args
		ann_list = deserialize(ann_list)
		init_id = int(init_id)

		if init_id != self.server_id:
			if init_id == Constants.INIT_ID:
				init_id = self.server_id
				ann_list = self.ltp_list

			# update, shuffle, and serialize announcement list
			ann_list = self.announcement_fwd(ann_list)
			ann_list = self.verifiable_shuffle(ann_list)
			ann_list = serialize(ann_list)

			# pass announcement list to next server
			send(self.next_addr, [Constants.NEW_ANNOUNCEMENT, ann_list, init_id])
		else:
			# initialize add announcement
			ann_list = serialize(ann_list)
			ann_args = [ann_list, Constants.INIT_ID]
			self.replace_stp(Constants.REPLACE_STP, ann_args)

	def replace_stp(self, msg_head, msg_args):
		ann_list, init_id = msg_args
		ann_list = deserialize(ann_list)
		init_id = int(init_id)
		if init_id == self.server_id:
			return

		if init_id == Constants.INIT_ID:
			init_id = self.server_id

		# add announcement list to current server and update next server
		self.stp_list = ann_list
		ann_list = serialize(ann_list)
		send(self.next_addr, [Constants.REPLACE_STP, ann_list, init_id])

	def new_message(self, msg_head, msg_args):
		client_msg, client_stp, client_sig = msg_args
		client_stp = int(client_stp)
		client_sig = int(client_sig)

		# [TODO] verify message, short-term pseudonym, and signature
		client_rep = self.stp_list[client_stp]
		send(self.board_addr, [Constants.POST_MESSAGE, client_msg, client_stp, client_rep])

	def new_feedback(self, msg_head, msg_args):
		client_msg_id, client_vote, client_sig = [int(_) for _ in msg_args]

		# [TODO] verify vote and linkable ring signature
		send(self.board_addr, [Constants.POST_FEEDBACK, client_msg_id, client_vote])

	# [NOTE] must initiate rev announcement on prev of leader
	def rev_announcement(self, msg_head, msg_args):
		ann_list, init_id = msg_args
		ann_list = deserialize(ann_list)
		init_id = int(init_id)

		if init_id != self.server_id:
			if init_id == Constants.INIT_ID:
				init_id = self.server_id
				ann_list = self.stp_list

			# update, shuffle, and serialize announcement list
			ann_list = self.announcement_bwd(ann_list)
			ann_list = self.verifiable_shuffle(ann_list)
			ann_list = serialize(ann_list)

			# pass announcement list to next server
			send(self.prev_addr, [Constants.REV_ANNOUNCEMENT, ann_list, init_id])
		else:
			# initialize add announcement
			ann_list = serialize(ann_list)
			ann_args = [ann_list, Constants.INIT_ID]
			self.replace_ltp(Constants.REPLACE_LTP, ann_args)

	def replace_ltp(self, msg_head, msg_args):
		ann_list, init_id = msg_args
		ann_list = deserialize(ann_list)
		init_id = int(init_id)
		if init_id == self.server_id:
			return

		if init_id == Constants.INIT_ID:
			init_id = self.server_id

		# add announcement list to current server and update next server
		self.ltp_list = ann_list
		ann_list = serialize(ann_list)
		send(self.next_addr, [Constants.REPLACE_LTP, ann_list, init_id])

	def update_neighbors(self, msg_head, msg_args):
		self.sprint('New Neighbors:')
		self.sprint('Prev: {}'.format((msg_args[0], msg_args[1])))
		self.sprint('Next: {}'.format((msg_args[2], msg_args[3])))
		self.set_prev_server(msg_args[0], int(msg_args[1]))
		self.set_next_server(msg_args[2], int(msg_args[3]))

	def update_next_server(self, msg_head, msg_args):
		self.sprint('New next server: {}'.format((msg_args[0], msg_args[1])))
		self.set_next_server(msg_args[0], int(msg_args[1]))

	def update_prev_server(self, msg_head, msg_args):
		self.sprint('New prev server: {}'.format((msg_args[0], msg_args[1])))
		self.set_prev_server(msg_args[0], int(msg_args[1]))

	def run(self):
		while True:
			# accept and receive socket message
			s, addr = self.ss.accept()
			msg = recv(s)
			s.close()

			# verify message information
			if not self.verify_message(msg):
				self.eprint('Error processing message.')
				continue

			msg_head, *msg_args = msg

			# respond to received message
			self.respond[msg_head](msg_head, msg_args)

if __name__ == '__main__':
	if len(sys.argv) != 4:
		print('USAGE: python server.py host port server_id')
		sys.exit(1)
	c = Server(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
	c.run()