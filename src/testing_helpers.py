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

#############################
# Change coordinator phase
#############################

def begin_client_registration(co, sleep=0.05):
	co.begin_client_registration()
	time.sleep(sleep)


def start_message_phase(co, sleep=0.01):
	co.begin_announcement_phase()
	while co.phase != Constants.MESSAGE_PHASE:
		time.sleep(sleep)


def start_feedback_phase(co):
	co.begin_feedback_phase()


def start_coinshuffle_phase(co):
	co.board.start_coinshuffle();
	while co.phase != Constants.COINSHUFFLE_FINISHED_PHASE:
		time.sleep(0.01)


def end_round(co, sleep=0.05):
	co.end_round()
	while co.phase != Constants.ANNOUNCEMENT_PHASE:
		time.sleep(sleep)

#############################
# Client functions
#############################

def post(c, msg, sleep=0.05):
	c.post(msg)
	time.sleep(sleep)


def post_blockchain(c, msg, rep, sleep=0.05):
	c.post(msg, rep)
	time.sleep(sleep)


def vote(c, amount, msg_id, sleep=0.05):
	c.vote(amount, msg_id)
	time.sleep(sleep)


def show(c):
	c.show()
