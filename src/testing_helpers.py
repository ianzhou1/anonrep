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
	tcp.bind(('', 0))
	addr, port = tcp.getsockname()
	tcp.close()
	return port

#############################
# Instantiators
#############################

def create_coordinator(sleep=0.1):
	co = Coordinator('localhost', get_free_port())
	config.COORDINATOR_ADDR = co.addr
	Thread(target=co.run, daemon=True).start()
	time.sleep(sleep)
	return co

def create_blockchain_coordinator(sleep=0.05):
	co = BlockchainCoordinator('localhost', get_free_port())
	config.COORDINATOR_ADDR = co.addr
	Thread(target=co.run, daemon=True).start()
	time.sleep(sleep)
	return co

def create_server(port=get_free_port(), sleep=0.01):
	s = Server('localhost', port)
	Thread(target=s.run, daemon=True).start()
	time.sleep(sleep)
	return s

def create_blockchain_server(port=get_free_port(), sleep=0.05):
	s = BlockchainServer('localhost', port)
	Thread(target=s.run, daemon=True).start()
	time.sleep(sleep)
	return s

def create_client(s, sleep=0.01):
	c = Client('localhost', s.addr[1])
	time.sleep(sleep)
	return c

def create_blockchain_client(s, sleep=0.05):
	c = BlockchainClient('localhost', s.addr[1])
	time.sleep(sleep)
	return c

#############################
# Change coordinator phase
#############################

def begin_client_registration(co, sleep=0.05):
	co.begin_client_registration()
	time.sleep(sleep)

def start_message_phase(co, sleep=0.01):
	co.begin_announcement_phase()
	try:
		co.board.begin_message_phase()
	except:
		pass
	while co.phase != Constants.MESSAGE_PHASE:
		time.sleep(sleep)

def start_feedback_phase(co):
	co.begin_feedback_phase()

def start_coinshuffle_phase(co):
	co.board.end_feedback_phase()
	co.board.start_coinshuffle();
	while co.phase != Constants.COINSHUFFLE_FINISHED_PHASE:
		time.sleep(0.01)

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

def show(c, sleep=0.05):
	c.show()
	time.sleep(sleep)
