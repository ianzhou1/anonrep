import socket
import sys
import traceback

import config
from util import Constants, randkey, powm, send, recv
from Crypto.PublicKey import ElGamal

# server class
class Server:
	def __init__(self, host, port):
		# identification
		self.server_id = Constants.INIT_ID
		self.prev_addr = None
		self.next_addr = None

		# core variables
		self.eph_key = None
		self.pri_key = randkey()
		self.pub_key = powm(Constants.G, self.pri_key)
		self.ltp_list = {} # long-term pseudonyms and encrypted reputation scores
		self.stp_list = {} # short-term pseudonyms and decrypted reputation scores

		# socket variables
		self.addr = (host, port)
		self.ss = socket.socket()
		self.ss.bind(self.addr)
		self.ss.listen(5)

		send(config.COORDINATOR_ADDR, [Constants.NEW_SERVER, self.addr, self.pub_key])

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
				Constants.UPDATE_ID: self.update_id,
				Constants.UPDATE_NEIGHBORS: self.update_neighbors,
		}

		# message type dict for received messages
		self.msg_types = {
				Constants.NEW_CLIENT: [int],
				Constants.NEW_REPUTATION: [int, list, int],
				Constants.ADD_REPUTATION: [int, list],
				Constants.NEW_ANNOUNCEMENT: [list, int],
				Constants.REPLACE_STP: [list, int],
				Constants.NEW_MESSAGE: [str, int, int],
				Constants.NEW_FEEDBACK: [int, int, int],
				Constants.REV_ANNOUNCEMENT: [list, int],
				Constants.REPLACE_LTP: [list, int],
				Constants.UPDATE_ID: [int],
				Constants.UPDATE_NEIGHBORS: [list, list],
		}

		assert set(self.respond.keys()) == set(self.msg_types.keys())

	def sprint(self, s):
		print('[SERVER] ' + s)

	def eprint(self, err):
		print('[SERVER] ' + err, file=sys.stderr)

	def set_prev_server(self, prev_addr):
		self.prev_addr = prev_addr

	def set_next_server(self, next_addr):
		self.next_addr = next_addr

	def encrypt(self, ltp, rep, server_pub_keys):
		# ElGamal encryption
		key = randkey()
		secret, text = rep

		secret = (secret * powm(Constants.G, key)) % Constants.MOD
		text = (text * powm(secret, self.pri_key)) % Constants.MOD
		for server_pub_key in server_pub_keys:
			text = (text * powm(server_pub_key, key)) % Constants.MOD

		return (secret, text)

	def decrypt(self, ltp, rep):
		# ElGamal decryption
		secret, text = rep

		text = (text * powm(secret, Constants.MOD - 2)) % Constants.MOD

		return (secret, text)

	def announcement_fwd(self, ann_list):
		self.eph_key = randkey()

		# [TODO] replace with forward encrypt (nym) and decrypt (rep)
		ret = ann_list
		return ret

	def announcement_bwd(self, ann_list):
		# [TODO] replace with backward decrypt (nym) and encrypt (rep)
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
		ret = ret and (len(msg_args) == len(self.msg_types[msg_head]))

		# verify that all arguments are of the appropriate type
		for i in range(len(msg_args)):
			ret = ret and isinstance(msg_args[i], self.msg_types[msg_head][i])

		return ret

	def new_client(self, msg_head, msg_args):
		client_ltp = msg_args[0]
		client_rep = Constants.INIT_REPUTATION

		# initiate new reputation
		rep_args = [client_ltp, client_rep, Constants.INIT_ID]
		self.new_reputation(Constants.NEW_REPUTATION, rep_args)

	def new_reputation(self, msg_head, msg_args):
		client_ltp, client_rep, init_id = msg_args

		if init_id != self.server_id:
			if init_id == Constants.INIT_ID:
				init_id = self.server_id

			self.sprint('New client with long-term pseudonym: {}'.format(client_ltp))

			# encrypt client reputation
			client_rep = self.encrypt(client_ltp, client_rep, [])

			# pass reputation to next server
			send(self.next_addr, [Constants.NEW_REPUTATION, client_ltp, client_rep, init_id])
		else:
			# initiate add reputation
			rep_args = [client_ltp, client_rep]
			self.add_reputation(Constants.ADD_REPUTATION, rep_args)

	def add_reputation(self, msg_head, msg_args):
		client_ltp, client_rep = msg_args
		if client_ltp in self.ltp_list:
			return

		# add reputation to current server and update next server
		self.ltp_list[client_ltp] = client_rep
		send(self.next_addr, [Constants.ADD_REPUTATION, client_ltp, client_rep])

	def new_announcement(self, msg_head, msg_args):
		ann_list, init_id = msg_args

		if init_id != self.server_id:
			if init_id == Constants.INIT_ID:
				init_id = self.server_id
				ann_list = [(k, v) for k, v in self.ltp_list.items()]

			# update and shuffle announcement list
			ann_list = self.announcement_fwd(ann_list)
			ann_list = self.verifiable_shuffle(ann_list)

			# pass announcement list to next server
			send(self.next_addr, [Constants.NEW_ANNOUNCEMENT, ann_list, init_id])
		else:
			# initialize add announcement
			ann_args = [ann_list, Constants.INIT_ID]
			self.replace_stp(Constants.REPLACE_STP, ann_args)

	def replace_stp(self, msg_head, msg_args):
		ann_list, init_id = msg_args

		# tell coordinator that announcement phase is finished
		if init_id == self.server_id:
			send(config.COORDINATOR_ADDR, [Constants.END_ANNOUNCEMENT_PHASE])
			return

		if init_id == Constants.INIT_ID:
			init_id = self.server_id

		# add announcement list to current server and update next server
		self.sprint("Announcement phase finished. Updated short-term pseudonyms.")
		self.stp_list = {k: v for (k, v) in ann_list}
		print(self.stp_list)
		send(self.next_addr, [Constants.REPLACE_STP, ann_list, init_id])

	def new_message(self, msg_head, msg_args):
		client_msg, client_stp, client_sig = msg_args

		# [TODO] verify message, short-term pseudonym, and signature
		client_rep = self.stp_list[client_stp]
		client_score = client_rep[1]
		send(config.COORDINATOR_ADDR, [Constants.POST_MESSAGE, client_msg, client_stp, client_score])

	def new_feedback(self, msg_head, msg_args):
		client_msg_id, client_vote, client_sig = [int(_) for _ in msg_args]

		# [TODO] verify vote and linkable ring signature
		send(config.COORDINATOR_ADDR, [Constants.POST_FEEDBACK, client_msg_id, client_vote])

	# [NOTE] must initiate rev announcement on prev of leader
	def rev_announcement(self, msg_head, msg_args):
		ann_list, init_id = msg_args

		if init_id != self.server_id:
			if init_id == Constants.INIT_ID:
				init_id = self.server_id
				ann_list = [(k, v) for k, v in self.stp_list.items()]

			# update and shuffle announcement list
			ann_list = self.announcement_bwd(ann_list)
			ann_list = self.verifiable_shuffle(ann_list)

			# pass announcement list to next server
			send(self.prev_addr, [Constants.REV_ANNOUNCEMENT, ann_list, init_id])
		else:
			# initialize add announcement
			ann_args = [ann_list, Constants.INIT_ID]
			self.replace_ltp(Constants.REPLACE_LTP, ann_args)

	def replace_ltp(self, msg_head, msg_args):
		ann_list, init_id = msg_args

		# tell coordinator that it's time to start a new round
		if init_id == self.server_id:
			send(config.COORDINATOR_ADDR, [Constants.END_MESSAGE_PHASE])
			return

		if init_id == Constants.INIT_ID:
			init_id = self.server_id

		# add announcement list to current server and update next server
		self.ltp_list = {k: v for (k, v) in ann_list}
		send(self.next_addr, [Constants.REPLACE_LTP, ann_list, init_id])

	def update_id(self, msg_head, msg_args):
		self.server_id = msg_args[0]
		self.sprint('Server id: {}'.format(self.server_id))

	def update_neighbors(self, msg_head, msg_args):
		prev_addr, next_addr = msg_args
		prev_addr = tuple(prev_addr)
		next_addr = tuple(next_addr)
		
		self.set_prev_server(prev_addr)
		self.set_next_server(next_addr)

	def run(self):
		while True:
			try:
				# accept and receive socket message
				s, addr = self.ss.accept()
				msg = recv(s)
				s.close()

				# verify message information
				if not self.verify_message(msg):
					self.eprint('Error processing ' + msg + '.')
					continue

				msg_head, *msg_args = msg

				# respond to received message
				self.respond[msg_head](msg_head, msg_args)
			except Exception:
				traceback.print_exc()

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('USAGE: python server.py host port')
		sys.exit(1)

	server_host = sys.argv[1]
	server_port = int(sys.argv[2])
	s = Server(server_host, server_port)
	
	try:
		s.run()
	finally:
		s.ss.close()
