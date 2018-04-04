import socket
import sys
import time
import traceback
from threading import Thread

import config
from board import MessageBoard
from util import Constants, send, recv, serialize



# coordinator server
class Coordinator:
	def __init__(self, host, port):
		self.addr = (host, port)
		self.ss = socket.socket()
		self.ss.bind(self.addr)
		self.ss.listen(5)

		self.phase = Constants.ANNOUNCEMENT_PHASE
		self.board = MessageBoard(self)

		# list of (server_host, server_port)
		self.servers = []
		# set of server_id's
		self.ids = set()

		sys.stdout.write('\r# servers: 0 | []')
		sys.stdout.flush()

		# respond dict for received messages
		self.respond = {
				Constants.NEW_SERVER: self.new_server,
				Constants.END_ANNOUNCEMENT_PHASE: self.end_announcement_phase,
		}

		# message length dict for received messages
		self.msg_lens = {
				Constants.NEW_SERVER: 3,
				Constants.END_ANNOUNCEMENT_PHASE: 0,
		}

		assert set(self.respond.keys()) == set(self.msg_lens.keys())

	def eprint(self, err):
		print('[COORDINATOR] ' + err, file=sys.stderr)

	def sprint(self, s):
		print('[COORDINATOR] ' + s)

	def new_server(self, msg_head, msg_args):
		# parse args
		server_host, server_port, server_id = msg_args
		if server_id in self.ids:
			self.eprint('Could not add {}: Duplicate ID'.format(msg_args))
			return
		self.ids.add(server_id)

		# add server to ring
		server_addr = (server_host, server_port)

		if len(self.servers) == 0:
			send(server_addr,
				[Constants.UPDATE_NEIGHBORS, server_host, server_port, server_host, server_port])
		else:
			prev_serv, next_serv = self.servers[-1], self.servers[0]

			send(prev_serv, [Constants.UPDATE_NEXT_SERVER, server_host, server_port])
			send(next_serv, [Constants.UPDATE_PREV_SERVER, server_host, server_port])

			send(server_addr,
				[Constants.UPDATE_NEIGHBORS, prev_serv[0], prev_serv[1], next_serv[0], next_serv[1]])
		self.servers.append((server_host, server_port))
		sys.stdout.write('\r# servers: {} | {}'.format(len(self.servers), self.servers))
		sys.stdout.flush()

	def end_announcement_phase(self, msg_head, msg_args):
		self.sprint('Beginning message phase...')
		self.phase = Constants.MESSAGE_PHASE

	def begin_announcement_phase(self):
		self.sprint('Beginning announcement phase...')
		# TODO: Randomly pick the initial
		server_addr = self.servers[0]
		send(server_addr, [Constants.NEW_ANNOUNCEMENT, serialize({}), Constants.INIT_ID])

	def end_round(self):
		# TODO: Don't hardcode the leader
		send(self.servers[-1], [Constants.REV_ANNOUNCEMENT, serialize({}), Constants.INIT_ID])

	def verify_message(self, msg):
		if len(msg) == 0:
			return False

		msg_head, *msg_args = msg

		# verify that msg_head is in respond dict
		ret = (msg_head in self.respond)

		# verify that msg_args length matches expected
		ret = ret or (len(msg_args) == self.msg_lens[msg_head])

		# verify that all arguments are of the appropriate type
		try:
			if msg_head == Constants.NEW_SERVER:
				int(msg_args[1])
				int(msg_args[2])
		except ValueError:
			ret = False

		return ret

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

				if self.phase != Constants.ANNOUNCEMENT_PHASE:
					self.board.process_message(s, msg, self.phase)
					continue

				# verify message information
				if not self.verify_message(msg):
					self.eprint('Error processing message.')
					continue

				msg_head, *msg_args = msg

				# respond to received message
				self.respond[msg_head](msg_head, msg_args)

				s.close()
			except ConnectionAbortedError:
				print()
				self.ss.close()
				break
			except Exception:
				traceback.print_exc()
		self.ss.close()

if __name__ == '__main__':
	if len(sys.argv) != 1:
		print('USAGE: python coordinator.py')
		sys.exit(1)
	print('*** Press [ENTER] once the first announcement phase is ready to begin. ***')
	c = Coordinator(config.COORDINATOR_SERVER, config.COORDINATOR_PORT)
	try:
		thread = Thread(target=c.run)
		thread.start()

		# Don't begin announcement phase until user presses enter
		input()
		while True:
			c.begin_announcement_phase()
			while c.phase != Constants.MESSAGE_PHASE:
				time.sleep(0.1)
			# message phase has begun
			time.sleep(Constants.MESSAGE_PHASE_LENGTH_IN_SECS)
			c.sprint('Beginning feedback phase...')
			c.phase = Constants.FEEDBACK_PHASE
			time.sleep(Constants.FEEDBACK_PHASE_LENGTH_IN_SECS)
			c.end_round()
			while c.phase == Constants.FEEDBACK_PHASE:
				time.sleep(0.1)
	finally:
		c.ss.close()