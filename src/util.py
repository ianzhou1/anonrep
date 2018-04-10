import socket
import json
from random import randint
from functools import singledispatch

# constants class
class Constants:
	MOD = 65537 # prime modulo
	G = 1848 # primitive root of MOD
	INTEGER_SIZE = 8 # number of bytes that will be used to denote the size of payload
	BUFFER_SIZE = 4096 # socket buffer receive buffer size
	ENCODING = 'UTF-8' # socket encoding
	INIT_REPUTATION = (1, 0) # initial reputation
	INIT_FEEDBACK = (0, 0) # initial feedback
	INIT_ID = -1 # id indicating initial phase

	MESSAGE_PHASE_LENGTH_IN_SECS = 10
	FEEDBACK_PHASE_LENGTH_IN_SECS = 10

	# coordinator phases
	ANNOUNCEMENT_PHASE = 'ANNOUNCEMENT_PHASE'
	MESSAGE_PHASE = 'MESSAGE_PHASE'
	FEEDBACK_PHASE = 'FEEDBACK_PHASE'

	# coordinator server headers
	NEW_SERVER = 'NEW_SERVER'
	END_ANNOUNCEMENT_PHASE = 'END_ANNOUNCEMENT_PHASE'

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
	END_MESSAGE_PHASE = 'END_MESSAGE_PHASE'

	# headers requiring open socket
	OPEN_SOCKET = set([DISP_BOARD])

	# message board keys
	MSG = 'msg' # message
	NYM = 'nym' # short-term pseudonym
	REP = 'rep' # reputation score
	FB = 'fb' # feedback

# send string through socket
@singledispatch
def send(s, msg):
	payload = json.dumps(msg).encode(Constants.ENCODING)
	s.send(len(payload).to_bytes(Constants.INTEGER_SIZE, byteorder='big') + payload)

@send.register(tuple)
def _(addr, msg):
	s = socket.socket()
	s.connect(addr)
	send(s, msg)

# recv string through socket
def recv(s):
	remaining = int.from_bytes(s.recv(Constants.INTEGER_SIZE), byteorder='big')
	chunks = []
	while remaining > 0:
		chunk = s.recv(min(Constants.BUFFER_SIZE, remaining))
		remaining -= len(chunk)
		chunks.append(chunk)
	return json.loads(b''.join(chunks).decode(Constants.ENCODING))

def sendrecv(addr, msg):
	s = socket.socket()
	s.connect(addr)
	send(s, msg)
	return recv(s)

# modular exponentiation
def powm(base, exp, mod=Constants.MOD):
	return pow(base, exp, mod)

# random key
def randkey(start=0, end=Constants.MOD):
	return randint(start, end)

# serialize container
def serialize(c):
	return json.dumps(c, separators=(',', ':'))

# deserialize container
def deserialize(s):
	c = json.loads(s)
	if not isinstance(c, dict) and not isinstance(c, list):
		raise ValueError
	return c
