import socket
import sys
import json
from random import randint
from functools import singledispatch


class Constants:
	MOD = 66071  # prime modulo (only used for printing shorter nyms)
	# G = int('A4D1CBD5C3FD34126765A442EFB99905F8104DD258AC507FD640' +
	# 		'6CFF14266D31266FEA1E5C41564B777E690F5504F213160217B4B01B' +
	# 		'886A5E91547F9E2749F4D7FBD7D3B9A92EE1909D0D2263F80A76A6A2' +
	# 		'4C087A091F531DBF0A0169B6A28AD662A4D18E73AFA32D779D5918D0' +
	# 		'8BC8858F4DCEF97C2A24855E6EEB22B3B2E5', 16) # generator
	# P = int('B10B8F96A080E01DDE92DE5EAE5D54EC52C99FBCFB06A3C69A6A' +
	# 		'9DCA52D23B616073E28675A23D189838EF1E2EE652C013ECB4AEA906' +
	# 		'112324975C3CD49B83BFACCBDD7D90C4BD7098488E9C219A73724EFF' +
	# 		'D6FAE5644738FAA31A4FF55BCCC0A151AF5F0DC8B4BD45BF37DF365C' +
	# 		'1A65E68CFDA76D4DA708DF1FB2BC2E4A4371', 16) # prime modulo
	# Q = int('F518AA8781A8DF278ABA4E7D64B7CB9D49462353', 16) # subgroup

	# G = 190
	# P = 66071
	# Q = 6607
	G = 2203
	P = 16000393
	Q = 666683

	INTEGER_SIZE = 8  # number of bytes that will be used to denote the size of payload
	BUFFER_SIZE = 4096  # socket buffer receive buffer size
	ENCODING = 'UTF-8'  # socket encoding
	INIT_SECRET = 1  # initial secret
	INIT_REPUTATION = 1  # initial reputation
	INIT_FEEDBACK = [0, 0]  # initial feedback
	INIT_ID = -1  # id indicating initial phase

	AES_KEY_LENGTH = 16  # length of AES key for CoinShuffle
	RSA_KEY_LENGTH = 2048  # length of RSA key for CoinShuffle

	MESSAGE_PHASE_LENGTH_IN_SECS = 6
	FEEDBACK_PHASE_LENGTH_IN_SECS = 6

	# general headers
	SUCCESS = 'SUCCESS'
	FAIL = 'FAIL'

	# coordinator phases
	REGISTRATION_PHASE = 'REGISTRATION_PHASE'
	ANNOUNCEMENT_PHASE = 'ANNOUNCEMENT_PHASE'
	MESSAGE_PHASE = 'MESSAGE_PHASE'
	FEEDBACK_PHASE = 'FEEDBACK_PHASE'

	# coordinator blockchain phases
	COINSHUFFLE_PHASE = 'COINSHUFFLE_PHASE'
	COINSHUFFLE_FINISHED_PHASE = 'COINSHUFFLE_FINISHED_PHASE'
	VOTE_CALCULATION_PHASE = 'VOTE_CALCULATION_PHASE'

	# coordinator server headers
	NEW_SERVER = 'NEW_SERVER'
	END_ANNOUNCEMENT_PHASE = 'END_ANNOUNCEMENT_PHASE'

	# blockchain coordinator server headers
	GET_CONTRACT_ADDRESS = 'GET_CONTRACT_ADDRESS'

	# coinshuffle coordinator message headers
	PARTICIPATION_STATUS = 'PARTICIPATION_STATUS'
	KEYS = 'KEYS'
	SHUFFLE = 'SHUFFLE'

	# server message headers
	NEW_CLIENT = 'NEW_CLIENT'
	NEW_REPUTATION = 'NEW_REPUTATION'
	NEW_ANNOUNCEMENT = 'NEW_ANNOUNCEMENT'
	REPLACE_STP = 'REPLACE_STP'
	NEW_MESSAGE = 'NEW_MESSAGE'
	NEW_FEEDBACK = 'NEW_FEEDBACK'
	REV_ANNOUNCEMENT = 'REV_ANNOUNCEMENT'
	REPLACE_LTP = 'REPLACE_LTP'
	UPDATE_ID = 'UPDATE_ID'
	UPDATE_NEIGHBORS = 'UPDATE_NEIGHBORS'
	GET_GENERATOR = 'GET_GENERATOR'
	GET_STP_ARRAY = 'GET_STP_ARRAY'
	GET_CIPHERTEXTS = 'GET_CIPHERTEXTS'
	GET_CLIENTS = 'GET_CLIENTS'
	UPDATE_CLIENTS = 'UPDATE_CLIENTS'

	# blockchain server message headers
	GET_LTP_ARRAY = 'GET_LTP_ARRAY'

	# message board headers
	POST_MESSAGE = 'POST_MESSAGE'
	POST_FEEDBACK = 'POST_FEEDBACK'
	DISP_BOARD = 'DISP_BOARD'
	RESTART_ROUND = 'RESTART_ROUND'

	# headers requiring open socket
	OPEN_SOCKET = set([
			NEW_ANNOUNCEMENT,
			REV_ANNOUNCEMENT,
			GET_GENERATOR,
			GET_STP_ARRAY,
			GET_LTP_ARRAY,
			DISP_BOARD,
			NEW_FEEDBACK,
			GET_CONTRACT_ADDRESS,
			PARTICIPATION_STATUS,
			KEYS,
			GET_CIPHERTEXTS,
			GET_CLIENTS,
			UPDATE_CLIENTS,
			NEW_CLIENT])

	# message board keys
	MSG = 'msg' # message
	NYM = 'nym' # short-term pseudonym
	REP = 'rep' # reputation score
	FB = 'fb' # feedback


@singledispatch
def send(s, args):
	"""Send arguments through socket s."""
	msg = json.dumps(args).encode(Constants.ENCODING)
	s.send(len(msg).to_bytes(Constants.INTEGER_SIZE, byteorder='big') + msg)


@send.register(tuple)
def _(addr, args):
	s = socket.socket()
	s.connect(addr)
	send(s, args)


def sendbytes(addr, msg):
	"""Send raw bytes to addr."""
	s = socket.socket()
	s.connect(addr)
	s.send(len(msg).to_bytes(Constants.INTEGER_SIZE, byteorder='big') + msg)


def recv(s):
	"""Receive arguments through socket s."""
	remaining = int.from_bytes(s.recv(Constants.INTEGER_SIZE), byteorder='big')
	chunks = []
	while remaining > 0:
		chunk = s.recv(min(Constants.BUFFER_SIZE, remaining))
		remaining -= len(chunk)
		chunks.append(chunk)
	return json.loads(b''.join(chunks).decode(Constants.ENCODING))


def recvbytes(s):
	"""Receive bytes through socket s."""
	remaining = int.from_bytes(s.recv(Constants.INTEGER_SIZE), byteorder='big')
	chunks = []
	while remaining > 0:
		chunk = s.recv(min(Constants.BUFFER_SIZE, remaining))
		remaining -= len(chunk)
		chunks.append(chunk)
	return b''.join(chunks)


def sendrecv(addr, args):
	"""Like send() except it waits for a response and returns it."""
	s = socket.socket()
	s.connect(addr)
	send(s, args)
	return recv(s)


def powm(base, exp, mod=Constants.P):
	"""Modular exponentiation."""
	return pow(base, exp, mod)


def egcd(b, a):
	"""Extended euclidean algorithm."""
	x0, x1, y0, y1 = 1, 0, 0, 1
	while a != 0:
		q, b, a = b // a, a, b % a
		x0, x1 = x1, x0 - q * x1
		y0, y1 = y1, y0 - q * y1
	return  b, x0, y0


def gcd(b, a):
	"""Returns the greatest common denominator of b and a."""
	g, _, __ = egcd(b, a)
	return g


def modinv(num, mod=Constants.P):
	"""Modular inverse."""
	g, inv, _ = egcd(num, mod)
	return (inv % mod) if g == 1 else None


def divide(a, b, p=Constants.P):
	"""Modular division."""
	m = modinv(b, p)
	return (m * a) % p if m else None


def msg_hash(msg, hash_func, mod=Constants.P):
	"""Message hash function."""
	msg = msg.encode(Constants.ENCODING)
	return int(hash_func(msg).hexdigest(), 16) % mod


def randkey(start=0, end=Constants.Q - 1):
	"""Returns a random key."""
	return randint(start, end)


def randkeyRP(start=0, end=Constants.Q - 1):
	"""Returns a random key (relatively prime to end + 1)."""
	ret = randkey(start, end)
	while gcd(ret, end + 1) != 1:
		ret = randkey(start, end)
	return ret


def sprint(name, s):
	"""Prints."""
	print('[{}] {}'.format(name, s))


def eprint(name, err):
	"""Prints error."""
	print('[{}] {}'.format(name, err), file=sys.stderr)
