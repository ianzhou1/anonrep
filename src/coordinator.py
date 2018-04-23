import random
import socket
import sys
import time
import traceback
from threading import Thread

import config
from board import MessageBoard
from util import Constants, send, recv, eprint, sprint


class Coordinator:
	"""Base implementation of Coordinator server."""

	def __init__(self, host, port):
		self.name = 'COORDINATOR'

		# servers variables
		self.num_servers = 0
		self.servers = [] # list of ((host, port))

		# core variables
		self.phase = Constants.REGISTRATION_PHASE
		self.board = MessageBoard(self)

		# socket variables
		self.addr = (host, port)
		self.ss = socket.socket()
		self.ss.bind(self.addr)
		self.ss.listen(5)
		self.server_started = False

		sys.stdout.write('\r# servers: 0 | []')
		sys.stdout.flush()

		# respond dict for received messages
		self.respond = {
				Constants.NEW_SERVER: self.new_server,
				Constants.END_ANNOUNCEMENT_PHASE: self.end_announcement_phase,
		}

		# message type dict for received messages
		self.msg_types = {
				Constants.NEW_SERVER: [list, int],
				Constants.END_ANNOUNCEMENT_PHASE: [],
		}

		assert set(self.respond.keys()) == set(self.msg_types.keys())

	def verify_message(self, msg):
		"""Verifies that the incoming message is valid."""
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

	def new_server(self, msg_args):
		"""Handles the creation of a new server."""
		server_addr, server_pub_key = msg_args
		server_addr = tuple(server_addr)

		# update new server id
		server_id = self.num_servers
		send(server_addr, [Constants.UPDATE_ID, server_id])

		# add server to ring ((host, port))
		self.servers.append(server_addr)
		self.num_servers += 1

		sys.stdout.write(
			'\r# servers: {} | {}'.format(self.num_servers, self.servers))
		sys.stdout.flush()

	def end_announcement_phase(self, msg_args):
		"""Handles end of announcement phase."""
		sprint(self.name, 'Beginning message phase...')
		self.phase = Constants.MESSAGE_PHASE

	def broadcast_neighbors(self):
		"""Tells all servers about their neighbors."""
		for idx, server_addr in enumerate(self.servers):
			prev_idx = (idx - 1) % self.num_servers
			next_idx = (idx + 1) % self.num_servers
			prev_addr = self.servers[prev_idx]
			next_addr = self.servers[next_idx]
			send(server_addr, [Constants.UPDATE_NEIGHBORS, prev_addr, next_addr])

	def begin_client_registration(self):
		"""Begins the client registration phase."""
		sprint(self.name, 'Beginning client registration...')
		self.phase = Constants.REGISTRATION_PHASE

		# update servers and neighbors
		self.broadcast_neighbors()

	def begin_announcement_phase(self):
		"""Begins the announcement phase."""
		sprint(self.name, 'Beginning announcement phase...')
		self.phase = Constants.ANNOUNCEMENT_PHASE

		# shuffle list of servers
		random.shuffle(self.servers)

		# update servers and neighbors
		self.broadcast_neighbors()

		# pause before beginning announcement phase
		time.sleep(0.1)

		server_addr = self.servers[0]
		send(server_addr,
			[Constants.NEW_ANNOUNCEMENT, [], Constants.G, Constants.INIT_ID])

	def begin_feedback_phase(self):
		"""Begins the feedback phase."""
		sprint(self.name, 'Beginning feedback phase...')
		self.phase = Constants.FEEDBACK_PHASE

	def end_round(self):
		"""Sends signal to servers to end the round."""
		server_addr = self.servers[-1]
		send(server_addr, [Constants.REV_ANNOUNCEMENT, [], [], Constants.INIT_ID])

	def run(self):
		while True:
			try:
				# accept and receive socket message
				s, addr = self.ss.accept()
				msg = recv(s)

				# displaying a board can be done at any time
				if len(msg) > 0 and msg[0] == Constants.DISP_BOARD:
					self.board.process_message(s, msg, self.phase)
					continue

				if self.phase not in [Constants.REGISTRATION_PHASE,
						Constants.ANNOUNCEMENT_PHASE]:
					self.board.process_message(s, msg, self.phase)
					continue

				# verify message information
				if not self.verify_message(msg):
					eprint(self.name, 'Error processing ' + str(msg) + '.')
					continue

				msg_head, *msg_args = msg

				# respond to received message
				if msg_head in Constants.OPEN_SOCKET:
					self.respond[msg_head](s, msg_args)
				else:
					self.respond[msg_head](msg_args)
			except ConnectionAbortedError:
				print()
				self.ss.close()
				break
			except Exception:
				traceback.print_exc()
			finally:
				s.close()
		self.ss.close()


if __name__ == '__main__':
	if len(sys.argv) != 1:
		print('USAGE: python coordinator.py')
		sys.exit(1)

	print('*** Press [ENTER] to begin client registration. ***')
	c = Coordinator(config.COORDINATOR_SERVER, config.COORDINATOR_PORT)
	try:
		thread = Thread(target=c.run)
		thread.start()

		input()
		c.begin_client_registration()

		print('*** Press [ENTER] to begin announcement phase. ***')
		input()

		while True:
			# announcement phase
			c.begin_announcement_phase()
			while c.phase != Constants.MESSAGE_PHASE:
				time.sleep(0.1)

			# message phase
			time.sleep(Constants.MESSAGE_PHASE_LENGTH_IN_SECS)

			# feedback phase
			c.begin_feedback_phase()
			time.sleep(Constants.FEEDBACK_PHASE_LENGTH_IN_SECS)

			# end round and restart
			c.end_round()
			while c.phase != Constants.ANNOUNCEMENT_PHASE:
				time.sleep(0.1)
	finally:
		c.ss.close()
