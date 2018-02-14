import socket
from random import randint

# constants class
class Constants:
	MOD = 65537 # prime modulo
	G = 1848 # primitive root of MOD
	BUFFER_SIZE = 4096 # socket buffer receive buffer size
	ENCODING = 'UTF-8' # socket encoding
	INIT_REPUTATION = 0 # initial reputation

	NEW_CLIENT = 'NEW_CLIENT'
	NEW_REPUTATION = 'NEW_REPUTATION'
	ADD_REPUTATION = 'ADD_REPUTATION'

# send string through socket
def send(s, msg):
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
