import socket
import json
from random import randint
from functools import singledispatch

# constants class
class Constants:
	MOD = 65537 # prime modulo
	G = 1848 # primitive root of MOD
	BUFFER_SIZE = 4096 # socket buffer receive buffer size
	ENCODING = 'UTF-8' # socket encoding
	INIT_REPUTATION = 0 # initial reputation
	INIT_FEEDBACK = (0, 0) # initial feedback
	INIT_ID = -1 # id indicating initial phase

	# coordinator server headers
	NEW_SERVER = 'NEW_SERVER'

	# server message headers
	NEW_CLIENT = 'NEW_CLIENT'
	NEW_REPUTATION = 'NEW_REPUTATION'
	ADD_REPUTATION = 'ADD_REPUTATION'
	NEW_ANNOUNCEMENT = 'NEW_ANNOUNCEMENT'
	REPLACE_STP = 'REPLACE_STP'
	NEW_MESSAGE = 'NEW_MESSAGE'
	NEW_FEEDBACK = 'NEW_FEEDBACK'
	REV_ANNOUNCEMENT = 'REV_ANNOUNCEMENT'
	REPLACE_LTP = 'REPLACE_LTP'
	UPDATE_NEIGHBORS = 'UPDATE_NEIGHBORS'
	UPDATE_NEXT_SERVER = 'NEW_NEXT_SERVER'
	UPDATE_PREV_SERVER = 'NEW_PREV_SERVER'

	# message board headers
	POST_MESSAGE = 'POST_MESSAGE'
	POST_FEEDBACK = 'POST_FEEDBACK'
	DISP_BOARD = 'DISP_BOARD'

	# headers requiring open socket
	OPEN_SOCKET = set(DISP_BOARD)

	# message board keys
	MSG = 'msg' # message
	NYM = 'nym' # short-term pseudonym
	REP = 'rep' # reputation score
	FB = 'fb' # feedback

# send string through socket
@singledispatch
def send(s, msg):
	s.send(json.dumps(msg).encode(Constants.ENCODING))

@send.register(tuple)
def _(addr, msg):
	s = socket.socket()
	s.connect(addr)
	s.send(json.dumps(msg).encode(Constants.ENCODING))

# recv string through socket
def recv(s):
	return json.loads(s.recv(Constants.BUFFER_SIZE).decode(Constants.ENCODING))

# modular exponentiation
def powm(base, exp, mod=Constants.MOD):
	return pow(base, exp, mod)

# random key
def randkey(start=0, end=Constants.MOD):
	return randint(start, end)

# serialize dictionary
def serialize(d):
	return json.dumps(d, separators=(',', ':'))

# deserialize dictionary
def deserialize(s):
	d = json.loads(s)
	if not isinstance(d, dict):
		raise ValueError
	return d
