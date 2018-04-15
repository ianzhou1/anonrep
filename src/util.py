import socket
import json
import hashlib
from random import randint
from functools import singledispatch

# constants class
class Constants:
	MOD = 65537 # prime modulo
	G = 1848 # primitive root of MOD
	INTEGER_SIZE = 8 # number of bytes that will be used to denote the size of payload
	BUFFER_SIZE = 4096 # socket buffer receive buffer size
	ENCODING = 'UTF-8' # socket encoding
	INIT_REPUTATION = [1, 1] # initial reputation (secret, text)
	INIT_FEEDBACK = [0, 0] # initial feedback
	INIT_ID = -1 # id indicating initial phase

	MESSAGE_PHASE_LENGTH_IN_SECS = 10
	FEEDBACK_PHASE_LENGTH_IN_SECS = 10

	# coordinator phases
	REGISTRATION_PHASE = 'REGISTRATION_PHASE'
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
	UPDATE_ID = 'UPDATE_ID'
	UPDATE_NEIGHBORS = 'UPDATE_NEIGHBORS'
	GET_GENERATOR = 'GET_GENERATOR'

	# message board headers
	POST_MESSAGE = 'POST_MESSAGE'
	POST_FEEDBACK = 'POST_FEEDBACK'
	DISP_BOARD = 'DISP_BOARD'
	END_MESSAGE_PHASE = 'END_MESSAGE_PHASE'

	# headers requiring open socket
	OPEN_SOCKET = set([GET_GENERATOR, DISP_BOARD])

	# message board keys
	MSG = 'msg' # message
	NYM = 'nym' # short-term pseudonym
	REP = 'rep' # reputation score
	FB = 'fb' # feedback

# send arguments through socket
@singledispatch
def send(s, args):
	payload = json.dumps(args).encode(Constants.ENCODING)
	s.send(len(payload).to_bytes(Constants.INTEGER_SIZE, byteorder='big') + payload)

@send.register(tuple)
def _(addr, args):
	s = socket.socket()
	s.connect(addr)
	send(s, args)

# receive arguments through socket
def recv(s):
	remaining = int.from_bytes(s.recv(Constants.INTEGER_SIZE), byteorder='big')
	chunks = []
	while remaining > 0:
		chunk = s.recv(min(Constants.BUFFER_SIZE, remaining))
		remaining -= len(chunk)
		chunks.append(chunk)
	return json.loads(b''.join(chunks).decode(Constants.ENCODING))

# send and receive arguments through socket
def sendrecv(addr, args):
	s = socket.socket()
	s.connect(addr)
	send(s, args)
	return recv(s)

# modular exponentiation
def powm(base, exp, mod=Constants.MOD):
	return pow(base, exp, mod)

# extended euclidean algorithm
def egcd(b, a):
	x0, x1, y0, y1 = 1, 0, 0, 1
	while a != 0:
		q, b, a = b // a, a, b % a
		x0, x1 = x1, x0 - q * x1
		y0, y1 = y1, y0 - q * y1
	return  b, x0, y0

# greatest common denominator
def gcd(b, a):
	g, _, __ = egcd(b, a)
	return g

# modular inverse
def modinv(num, mod=Constants.MOD):
	g, inv, _ = egcd(num, mod)
	return (inv % mod) if g == 1 else None

# message hash function
def sighash(msg, mod=Constants.MOD):
	msg = msg.encode(Constants.ENCODING)
	return int(hashlib.sha1(msg).hexdigest(), 16) % Constants.MOD

# random key
def randkey(start=0, end=Constants.MOD - 1):
	return randint(start, end)

# random key (relatively prime)
def randkeyRP(start=0, end=Constants.MOD - 1):
	ret = randkey(start, end)
	while gcd(ret, end + 1) != 1:
		ret = randkey(start, end)
	return ret
