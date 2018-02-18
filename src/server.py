import sys
import socket
from util import *

# server class
class Server:
	def __init__(self, host, port, server_id):
		# identification
		self.server_id = server_id

		# core variables
		self.pri_key = randkey()
		self.pub_key = powm(Constants.G, self.pri_key)
		self.rep_list = {} # long-term pseudonyms and encrypted reputation scores
		self.nym_list = {} # short-term pseudonyms and decrypted reputation scores

		# socket variables
		self.addr = (host, port)
		self.ss = socket.socket()
		self.ss.bind(self.addr)
		self.ss.listen(5)

		# respond dict for received messages
		self.respond = {
				Constants.NEW_CLIENT:	self.new_client,
				Constants.NEW_REPUTATION: self.new_reputation,
				Constants.ADD_REPUTATION: self.add_reputation,
				Constants.NEW_ANNOUNCEMENT: self.new_announcement,
				Constants.ADD_ANNOUNCEMENT: self.add_announcement
		}

		# message length dict for received messages
		self.msg_lens = {
				Constants.NEW_CLIENT: 1,
				Constants.NEW_REPUTATION: 3,
				Constants.ADD_REPUTATION: 2,
				Constants.NEW_ANNOUNCEMENT: 2,
				Constants.ADD_ANNOUNCEMENT: 2
		}

		assert set(self.respond.keys()) == set(self.msg_lens.keys())

	def set_next_server(self, next_host, next_port):
		self.next_addr = (next_host, next_port)

	def encrypt(self, text):
		# [TODO] replace with ElGamal
		return text

	def decrypt(self, text):
		# [TODO] replace with ElGamal
		return text

	def announcement_update(self, ann_list):
		eph_key = randkey()

		# [TODO] replace with encrypt/decrypt
		ret = ann_list
		return ret

	def verifiable_shuffle(self, ann_list):
		# [TODO] replace with verifiable shuffle
		return ann_list

	def verify_message(self, msg_info):
		if len(msg_info) != 2:
			return False

		msg_head = msg_info[0]
		msg_args = msg_info[1].split()

		# verify that msg_head is in respond dict
		ret = (msg_head in self.respond)

		# verify that msg_args length matches expected
		ret = ret or (len(msg_args) == self.msg_lens[msg_head])

		# verify that all arguments are of the appropriate type
		try:
			if msg_head in [Constants.NEW_ANNOUNCEMENT, Constants.ADD_ANNOUNCEMENT]:
				ann_list = deserialize(msg_args[0])
				init_id = int(msg_args[1])
			else:
				msg_args = [int(_) for _ in msg_args]
		except ValueError:
			ret = False

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

			# encrypt client reputation
			client_rep = self.encrypt(client_rep)

			# pass reputation to next server
			msg = '{} {} {} {}'.format(Constants.NEW_REPUTATION,
					client_ltp, client_rep, init_id)
			send(self.next_addr, msg)
		else:
			# initiate add reputation
			rep_args = [client_ltp, client_rep]
			self.add_reputation(Constants.ADD_REPUTATION, rep_args)

	def add_reputation(self, msg_head, msg_args):
		client_ltp, client_rep = msg_args
		if client_ltp in self.rep_list:
			return

		# add reputation to current server and update next server
		self.rep_list[client_ltp] = client_rep
		msg = '{} {} {}'.format(Constants.ADD_REPUTATION, client_ltp, client_rep)
		send(self.next_addr, msg)

	def new_announcement(self, msg_head, msg_args):
		ann_list, init_id = msg_args
		ann_list = deserialize(ann_list)

		if init_id != self.server_id:
			if init_id == Constants.INIT_ID:
				init_id = self.server_id
				ann_list = self.rep_list

			# update, shuffle, and serialize announcement list
			ann_list = self.announcement_update(ann_list)
			ann_list = self.verifiable_shuffle(ann_list)
			ann_list = serialize(ann_list)

			# pass announcement list to next server
			msg = '{} {} {}'.format(Constants.NEW_ANNOUNCEMENT, ann_list, init_id)
			send(self.next_addr, msg)
		else:
			# initialize add announcement
			ann_list = serialize(ann_list)
			ann_args = [ann_list, Constants.INIT_ID]
			self.add_announcement(Constants.ADD_ANNOUNCEMENT, ann_args)

	def add_announcement(self, msg_head, msg_args):
		ann_list, init_id = msg_args
		ann_list = deserialize(ann_list)
		if init_id == self.server_id:
			return

		if init_id == Constants.INIT_ID:
			init_id = self.server_id

		# add announcement list to current server and update next server
		self.nym_list = ann_list
		ann_list = serialize(ann_list)
		msg = '{} {} {}'.format(Constants.ADD_ANNOUNCEMENT, ann_list, init_id)
		send(self.next_addr, msg)

	def run(self):
		while True:
			# accept and receive socket message
			s, addr = self.ss.accept()
			msg = recv(s)
			s.close()

			msg_info = msg.split(maxsplit=1)

			# verify message information
			if not self.verify_message(msg_info):
				self.eprint('Error processing message.')
				continue

			msg_head = msg_info[0]
			msg_args = [int(_) for _ in msg_info[1].split()]

			# respond to received message
			self.respond[msg_head](msg_head, msg_args)


	def eprint(self, err):
		print('[SERVER] ' + err, file=sys.stderr)
