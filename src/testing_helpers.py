import config
import socket
import time

from coordinator import Coordinator
from server import Server
from client import Client
from coordinator_blockchain import BlockchainCoordinator
from server_blockchain import BlockchainServer
from client_blockchain import BlockchainClient
from util import Constants

from threading import Thread

def get_free_port():
	tcp = socket.socket()
	tcp.bind(('localhost', 0))
	addr, port = tcp.getsockname()
	tcp.close()
	return port

#############################
# Instantiators
#############################

def create_coordinator(port=None):
	if port is None:
		port = get_free_port()
	co = Coordinator('localhost', port)
	config.COORDINATOR_ADDR = co.addr
	Thread(target=co.run, daemon=True).start()
	return co


def create_blockchain_coordinator(port=None):
	if port is None:
		port = get_free_port()
	co = BlockchainCoordinator('localhost', port)
	config.COORDINATOR_ADDR = co.addr
	Thread(target=co.run, daemon=True).start()
	return co


def create_server(port=None, sleep=0.01):
	if port is None:
		port = get_free_port()
	s = Server('localhost', port)
	Thread(target=s.run, daemon=True).start()
	while not s.server_started:
		time.sleep(sleep)
	return s


def create_blockchain_server(port=None, sleep=0.01):
	if port is None:
		port = get_free_port()
	s = BlockchainServer('localhost', port)
	Thread(target=s.run, daemon=True).start()
	while not s.server_started:
		time.sleep(sleep)
	return s


def create_client(server):
	return Client('localhost', server.addr[1])


def create_blockchain_client(server):
	return BlockchainClient('localhost', server.addr[1])


class LocalBaseAnonRep:
	def __init__(self, num_servers, num_clients):
		"""Constructs coordinators, servers, and clients and keeps them organized

		num_servers: The number of servers
		num_clients: num_clients[i] is the number of clients server i has.
		"""
		assert(len(num_clients) == num_servers)

		self.co = create_coordinator()

		self.servers = [create_server() for _ in range(num_servers)]
		self.clients = []

		self.co.begin_client_registration()
		# wait for all servers to update neighbors
		while sum(s.prev_addr is not None for s in self.servers) == 0:
			time.sleep(0.01)

		for i, num in enumerate(num_clients):
			for _ in range(num):
				self.clients.append(create_client(self.servers[i]))

	def start_message_phase(self, sleep=0.01):
		self.co.begin_announcement_phase()
		while self.co.phase != Constants.MESSAGE_PHASE:
			time.sleep(sleep)

	def start_feedback_phase(self):
		self.co.begin_feedback_phase()

	def start_coinshuffle_phase(self):
		self.co.board.start_coinshuffle();
		while self.co.phase != Constants.COINSHUFFLE_FINISHED_PHASE:
			time.sleep(0.01)

	def end_round(self, sleep=0.05):
		self.co.end_round()
		while self.co.phase != Constants.ANNOUNCEMENT_PHASE:
			time.sleep(sleep)

	def post(self, idx, msg, sleep=0.01):
		old_len = len(self.co.board.board)
		self.clients[idx].post(msg)
		while len(self.co.board.board) == old_len:
			time.sleep(sleep)

	def vote(self, idx, amount, msg_id, sleep=0.01):
		old_fb = self.co.board.board[msg_id][1][Constants.FB]
		if not self.clients[idx].vote(amount, msg_id):
			return
		while self.co.board.board[msg_id][1][Constants.FB] == old_fb:
			time.sleep(sleep)


class LocalBlockchainAnonRep(LocalBaseAnonRep):
	def __init__(self, num_servers, num_clients):
		"""Constructs coordinators, servers, and clients and keeps them organized

		num_servers: The number of servers
		num_clients: num_clients[i] is the number of clients server i has.
		"""
		assert(len(num_clients) == num_servers)

		self.co = create_blockchain_coordinator()

		self.servers = [create_blockchain_server() for _ in range(num_servers)]
		self.clients = []

		self.co.begin_client_registration()
		# wait for all servers to update neighbors
		while sum(s.prev_addr is not None for s in self.servers) == 0:
			time.sleep(0.01)

		for i, num in enumerate(num_clients):
			for _ in range(num):
				self.clients.append(create_blockchain_client(self.servers[i]))

		self.co.update_servers()

	def end_round(self, sleep=0.05):
		# This shouldn't do anything in the blockchain version of AnonRep.
		pass

	def start_message_phase(self, sleep=0.01):
		self.co.begin_message_phase()

	def post(self, idx, msg, rep, sleep=0.01):
		old_len = len(self.co.board.board)
		if not self.clients[idx].post(msg, rep):
			return
		while len(self.co.board.board) == old_len:
			time.sleep(sleep)
