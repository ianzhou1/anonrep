import socket
import sys
import traceback
import random

import config
import lrs
import shuffle
from util import Constants, send, recv, powm, modinv, msg_hash, randkey
from hashlib import sha1

# server class
class Server:
	def __init__(self, host, port):
		# identification
		self.server_id = Constants.INIT_ID
		self.prev_addr = None
		self.next_addr = None

		# core variables
		self.eph_key = randkey()
		self.pri_key = randkey()
		self.pub_key = powm(Constants.G, self.pri_key)
		self.secret = None # secret used for encryption/decryption
		self.ltp_list = {} # long-term pseudonyms and encrypted reputation scores
		self.stp_list = {} # short-term pseudonyms and decrypted reputation scores
		self.stp_array = [] # short-term pseudonym array
		self.generator = None # round-based global generator
		self.nym_list = {} # pseudonym list used for decryption
		self.lrs_duplicates = set() # duplicate feedback set

		# socket variables
		self.addr = (host, port)
		self.ss = socket.socket()
		self.ss.bind(self.addr)
		self.ss.listen(5)
		self.server_started = False

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
				Constants.GET_GENERATOR: self.get_generator,
				Constants.GET_STP_ARRAY: self.get_stp_array,
		}

		# message type dict for received messages
		self.msg_types = {
				Constants.NEW_CLIENT: [int],
				Constants.NEW_REPUTATION: [int, int, int, list, int],
				Constants.ADD_REPUTATION: [int, int, int],
				Constants.NEW_ANNOUNCEMENT: [int, list, list, int, int, int],
				Constants.REPLACE_STP: [list, int, int],
				Constants.NEW_MESSAGE: [str, int, list],
				Constants.NEW_FEEDBACK: [int, str, int, list],
				Constants.REV_ANNOUNCEMENT: [int, list, list, list, int, int, int],
				Constants.REPLACE_LTP: [list, int, int],
				Constants.UPDATE_ID: [int],
				Constants.UPDATE_NEIGHBORS: [list, list],
				Constants.GET_GENERATOR: [],
				Constants.GET_STP_ARRAY: [],
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

	def encryptElGamal(self, rep, server_pub_keys):
		# ElGamal encryption
		for server_pub_key in server_pub_keys:
			rep = (rep * powm(server_pub_key, self.eph_key)) % Constants.P

		return rep

	def decryptElGamal(self, sec_inv, rep):
		# ElGamal decryption
		rep = (rep * sec_inv) % Constants.P

		return rep

	def announcement_fwd(self, ann_list, sec_inv):
		# forward encrypt (nym) and decrypt (rep)
		new_ann_list = [[], []]
		for nym in ann_list[0]:
			new_nym = powm(nym, self.eph_key)
			self.nym_list[new_nym] = nym
			new_ann_list[0].append(new_nym)
		for sec, rep in ann_list[1]:
			new_rep = self.decryptElGamal(sec_inv, rep)
			new_ann_list[1].append((sec, new_rep))

		return new_ann_list

	def announcement_bwd(self, ann_list, secret, server_pub_keys):
		# backward decrypt (nym) and encrypt (rep)
		new_ann_list = [[], []]
		for nym in ann_list[0]:
			new_nym = self.nym_list[nym]
			new_ann_list[0].append(new_nym)
		for sec, rep in ann_list[1]:
			new_rep = self.encryptElGamal(rep, server_pub_keys)
			new_ann_list[1].append((secret, new_rep))

		self.nym_list.clear()

		return new_ann_list

	def verify_message(self, msg):
		if len(msg) == 0:
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

	def verify_signature(self, msg, stp, sig):
		r, s = sig
		u = powm(self.generator, msg_hash(msg, sha1))
		v = (powm(stp, r) * powm(r, s)) % Constants.P
		return u == v

	def new_client(self, msg_args):
		client_ltp = msg_args[0]
		client_sec = Constants.INIT_SECRET
		client_rep = Constants.INIT_REPUTATION

		# initiate new reputation
		rep_args = [client_ltp, client_sec, client_rep, [], Constants.INIT_ID]
		self.new_reputation(rep_args)

	def new_reputation(self, msg_args):
		client_ltp, client_sec, client_rep, server_pub_keys, init_id = msg_args

		if init_id != self.server_id:
			if init_id == Constants.INIT_ID:
				init_id = self.server_id

			self.sprint('New client with long-term pseudonym: {}'.format(client_ltp % Constants.MOD))

			# encrypt client reputation
			server_pub_keys.append(self.pub_key)
			self.secret = powm(client_sec, self.pri_key)
			client_sec = (client_sec * powm(Constants.G, self.eph_key)) % Constants.P
			client_rep = (client_rep * self.secret) % Constants.P
			client_rep = self.encryptElGamal(client_rep, server_pub_keys)

			# pass reputation to next server
			send(self.next_addr, [Constants.NEW_REPUTATION, client_ltp, client_sec, client_rep, server_pub_keys, init_id])
		else:
			# initiate add reputation
			rep_args = [client_ltp, client_sec, client_rep]
			self.add_reputation(rep_args)

	def add_reputation(self, msg_args):
		client_ltp, client_sec, client_rep = msg_args
		if client_ltp in self.ltp_list:
			return

		# add reputation to current server and update next server
		self.secret = client_sec
		self.ltp_list[client_ltp] = client_rep
		send(self.next_addr, [Constants.ADD_REPUTATION, client_ltp, client_sec, client_rep])

	def new_announcement(self, s, msg_args):
		generator, ann_list_pre, ann_list_post, g_, h_, init_id = msg_args
		ann_list = ann_list_post

		if init_id != self.server_id:
			if init_id == Constants.INIT_ID:
				init_id = self.server_id
				ann_list = []
				ann_list.append([k for k in self.ltp_list.keys()])
				ann_list.append([(self.secret, v) for v in self.ltp_list.values()])

			else:
				# verify shuffle from prev server
				if not shuffle.verify(s, ann_list_pre[1], ann_list_post[1], g_, h_):
					self.eprint('Verifiable shuffle failed.')
					s.close()
					return

			s.close()

			# update announcement list
			secret_inv = modinv(powm(self.secret, self.pri_key))
			new_ann_list = self.announcement_fwd(ann_list, secret_inv)

			# shuffle announcement list
			n = len(new_ann_list[0])
			pi = shuffle.generate_permutation(n)
			new_ann_list = [shuffle.shuffle(elts, pi) for elts in new_ann_list]

			# update generator and parameters
			new_generator = powm(generator, self.eph_key)
			beta = 1
			g_ = 1
			h_ = secret_inv

			# pass announcement list to next server
			s = socket.socket()
			s.connect(self.next_addr)
			send(s, [Constants.NEW_ANNOUNCEMENT,
					new_generator, ann_list, new_ann_list, g_, h_, init_id])

			# prove shuffle to next server (if more than one server)
			if self.addr != self.next_addr:
				shuffle.prove(s, ann_list[1], new_ann_list[1], pi, beta, g_, h_)
		else:
			# verify shuffle from prev server (if more than one server)
			if self.addr != self.prev_addr:
				if not shuffle.verify(s, ann_list_pre[1], ann_list_post[1], g_, h_):
					self.eprint('Verifiable shuffle failed.')
					s.close()
					return

			s.close()

			# initialize add announcement
			stp_list = list(zip(ann_list[0], [rep for sec, rep in ann_list[1]]))
			stp_args = [stp_list, generator, Constants.INIT_ID]
			self.replace_stp(stp_args)

	def replace_stp(self, msg_args):
		stp_list, generator, init_id = msg_args
		self.generator = generator

		# tell coordinator that announcement phase is finished
		if init_id == self.server_id:
			send(config.COORDINATOR_ADDR, [Constants.END_ANNOUNCEMENT_PHASE])
			return

		if init_id == Constants.INIT_ID:
			init_id = self.server_id

		# add announcement list to current server
		self.sprint('Announcement phase finished. Updated short-term pseudonyms.')
		self.stp_list = {k: v for (k, v) in stp_list}
		self.stp_array = [k for (k, v) in stp_list]

		# modify for printing purposes
		stp_list_print = {}
		for k, v in stp_list:
			stp_list_print[k % Constants.MOD] = v
		print('stp list: ' + str(stp_list_print))

		# update next server
		send(self.next_addr, [Constants.REPLACE_STP, stp_list, generator, init_id])

	def get_generator(self, s, msg_args):
		# send global generator
		send(s, self.generator)

	def new_message(self, msg_args):
		client_msg, client_stp, client_sig = msg_args

		# verify message, pseudonym, and signature
		if not self.verify_signature(client_msg, client_stp, client_sig):
			self.eprint('Message signature verification failed.')
			return

		client_rep = self.stp_list[client_stp]
		send(config.COORDINATOR_ADDR, [Constants.POST_MESSAGE, client_msg, client_stp, client_rep])

	def get_stp_array(self, s, msg_args):
		# send short term pseudonym list
		send(s, self.stp_array)

	def new_feedback(self, s, msg_args):
		client_msg_id, client_msg, client_vote, client_sig = msg_args
		client_tag = client_sig[2]

		# verify vote
		if client_vote not in [-1, 1]:
			self.eprint('Invalid vote received.')
			send(s, [Constants.FAIL, 'Invalid vote amount.'])
			return

		# modify copy of stp_array to prevent duplicate voting
		stp_array = list(self.stp_array)
		stp_array.append(msg_hash(client_msg, sha1))

		# verify not a duplicate
		if client_tag in self.lrs_duplicates:
			self.eprint('Feedback linkable ring signature duplicate detected.')
			send(s, [Constants.FAIL, 'Duplicate vote.'])
			return

		# verify linkable ring signature
		if not lrs.verify(client_msg, stp_array, *client_sig, g=self.generator):
			self.eprint('Feedback linkable ring signature verification failed.')
			send(s, [Constants.FAIL, 'LRS verification failed.'])
			return

		self.lrs_duplicates.add(client_tag)
		send(config.COORDINATOR_ADDR, [Constants.POST_FEEDBACK, client_msg_id, client_vote])
		send(s, [Constants.SUCCESS])

	# [NOTE] must initiate rev announcement on prev of leader
	def rev_announcement(self, s, msg_args):
		secret, server_pub_keys, ann_list_pre, ann_list_post, g_, h_, init_id = msg_args
		ann_list = ann_list_post

		if init_id != self.server_id:
			if init_id == Constants.INIT_ID:
				init_id = self.server_id
				ann_list = []
				ann_list.append([k for k in self.stp_list.keys()])
				ann_list.append([(secret, v) for v in self.stp_list.values()])
			else:
				# verify shuffle from prev server
				if not shuffle.verify(s, ann_list_pre[1], ann_list_post[1], g_, h_):
					self.eprint('Verifiable shuffle failed.')
					s.close()
					return

			s.close()

			self.eph_key = randkey()

			# update announcement list
			server_pub_keys.append(self.pub_key)
			self.secret = powm(secret, self.pri_key)
			secret = (secret * powm(Constants.G, self.eph_key)) % Constants.P
			ann_list[1] = [(sec, (rep * self.secret) % Constants.P) for sec, rep in ann_list[1]]
			new_ann_list = self.announcement_bwd(ann_list, secret, server_pub_keys)

			# shuffle announcement list
			n = len(new_ann_list[0])
			pi = shuffle.generate_permutation(n)
			new_ann_list = [shuffle.shuffle(elts, pi) for elts in new_ann_list]

			# update parameters
			beta = self.eph_key
			g_ = Constants.G
			h_ = 1
			for server_pub_key in server_pub_keys:
				h_ = (h_ * server_pub_key) % Constants.P

			# pass announcement list to next server
			s = socket.socket()
			s.connect(self.prev_addr)
			send(s, [Constants.REV_ANNOUNCEMENT,
					secret, server_pub_keys, ann_list, new_ann_list, g_, h_, init_id])

			# prove shuffle to prev server
			if self.addr != self.prev_addr:
				shuffle.prove(s, ann_list[1], new_ann_list[1], pi, beta, g_, h_)
		else:
			# verify shuffle from next server (if more than one server)
			if self.addr != self.next_addr:
				if not shuffle.verify(s, ann_list_pre[1], ann_list_post[1], g_, h_):
					self.eprint('Verifiable shuffle failed.')
					s.close()
					return

			s.close()

			# initialize add announcement
			ltp_list = list(zip(ann_list[0], [rep for sec, rep in ann_list[1]]))
			ann_args = [ltp_list, secret, Constants.INIT_ID]
			self.replace_ltp(ann_args)

	def replace_ltp(self, msg_args):
		ltp_list, secret, init_id = msg_args
		self.secret = secret
		self.generator = None
		self.lrs_duplicates.clear()

		# tell coordinator that it's time to start a new round
		if init_id == self.server_id:
			send(config.COORDINATOR_ADDR, [Constants.RESTART_ROUND])
			return

		if init_id == Constants.INIT_ID:
			init_id = self.server_id

		# add announcement list to current server and update next server
		self.ltp_list = {k: v for (k, v) in ltp_list}

		# modify for printing purposes
		ltp_list_print = {}
		for k, v in ltp_list:
			ltp_list_print[k % Constants.MOD] = v % Constants.MOD
		print('ltp list: ' + str(ltp_list_print))
		send(self.next_addr, [Constants.REPLACE_LTP, ltp_list, secret, init_id])

	def update_id(self, msg_args):
		self.server_id = msg_args[0]
		self.sprint('Server id: {}'.format(self.server_id))

	def update_neighbors(self, msg_args):
		prev_addr, next_addr = msg_args
		prev_addr = tuple(prev_addr)
		next_addr = tuple(next_addr)

		self.set_prev_server(prev_addr)
		self.set_next_server(next_addr)
		send(config.COORDINATOR_ADDR, [Constants.UPDATE_NEIGHBORS])

	def run(self):
		while True:
			try:
				# accept and receive socket message
				s, addr = self.ss.accept()
				self.server_started = True
				msg = recv(s)

				# verify message information
				if not self.verify_message(msg):
					self.eprint('Error processing ' + str(msg) + '.')
					s.close()
					continue

				msg_head, *msg_args = msg

				# respond to received message
				if msg_head in Constants.OPEN_SOCKET:
					self.respond[msg_head](s, msg_args)
				else:
					self.respond[msg_head](msg_args)
				s.close()
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
