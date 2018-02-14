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
		self.rep_list = {}

		# socket variables
		self.addr = (host, port)
		self.ss = socket.socket()
		self.ss.bind(self.addr)
		self.ss.listen(5)

		# respond dict for received messages
		self.respond = {
				Constants.NEW_CLIENT:	self.new_client,
				Constants.NEW_REPUTATION: self.new_reputation,
				Constants.ADD_REPUTATION: self.add_reputation
		}

	def set_next_server(self, next_host, next_port):
		self.next_addr = (next_host, next_port)

	def encrypt(self, text):
		return powm(text, self.pub_key)

	def decrypt(self, text):
		pass

	def new_client(self, msg_args):
		# [TODO] verify args
		client_ltp = int(msg_args)
		client_rep = Constants.INIT_REPUTATION
		next_server = socket.socket()
		next_server.connect(self.next_addr)

		# new reputation
		msg = '{} {} {} {}'.format(
				Constants.NEW_REPUTATION,
				client_ltp,
				self.encrypt(client_rep),
				self.server_id
		)
		send(next_server, msg)

	def new_reputation(self, msg_args):
		# [TODO] verify args
		client_ltp, client_rep, init_id = [int(_) for _ in msg_args.split()]
		next_server = socket.socket()
		next_server.connect(self.next_addr)
		msg = ''

		if init_id == self.server_id:
			# return if pseudonym already in list
			if client_ltp in self.rep_list:
				return

			rep_list[client_ltp] = client_rep

			# add reputation to next server
			msg = '{} {} {}'.format(Constants.ADD_REPUTATION, client_ltp, client_rep)

		else:
			# encrypt reputation and pass to next server
			msg = '{} {} {} {}'.format(
					Constants.NEW_REPUTATION,
					client_ltp,
					self.encrypt(client_rep),
					init_id
			)

		send(next_server, msg)

	def add_reputation(self, msg_args):
		# [TODO] verify args
		client_ltp, client_rep = [int(_) for _ in msg_args.split()]
		next_server = socket.socket()
		next_server.connect(self.next_addr)

		rep_list[client_ltp] = client_rep

		# add reputation to next server
		msg = '{} {} {}'.format(Constants.ADD_REPUTATION, client_ltp, client_rep)
		send(next_server, msg)

	def run(self):
		while True:
			# accept and receive socket message
			s, addr = self.ss.accept()
			msg = recv(s)
			msg_info = msg.split(maxsplit=1)

			# verify message format
			if len(msg_info) != 2 or msg_info[0] not in self.respond:
				self.eprint('Error processing message.')
			else:
				# respond to received message
				msg_head, msg_args = msg_info
				self.respond[msg_head](self, msg_args)

			s.close()
			break

	def eprint(self, err):
		print('[SERVER] ' + err, file=sys.stderr)
