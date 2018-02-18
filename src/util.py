import socket
import json
from random import randint

# constants class
class Constants:
	MOD = 65537 # prime modulo
	G = 1848 # primitive root of MOD
	BUFFER_SIZE = 4096 # socket buffer receive buffer size
	ENCODING = 'UTF-8' # socket encoding
	INIT_REPUTATION = 0 # initial reputation
	INIT_ID = -1 # id indicating initial phase

	NEW_CLIENT = 'NEW_CLIENT'
	NEW_REPUTATION = 'NEW_REPUTATION'
	ADD_REPUTATION = 'ADD_REPUTATION'
	NEW_ANNOUNCEMENT = 'NEW_ANNOUNCEMENT'
	ADD_ANNOUNCEMENT = 'ADD_ANNOUNCEMENT'

# send string through socket
def send(addr, msg):
	s = socket.socket()
	s.connect(addr)
	s.send(msg.encode(Constants.ENCODING))

# recv string through socket
def recv(s):
	return s.recv(Constants.BUFFER_SIZE).decode(Constants.ENCODING)

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
