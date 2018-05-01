import io
import pprint
import random
import re
import socket
import sys
import traceback
from threading import Thread

import blockchain as bc
import config
import lrs

from client import Client
from util import Constants, msg_hash, recv, recvbytes, send, sendbytes, sendrecv, eprint
from hashlib import sha1
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes


class BlockchainClient(Client):
	"""Client implementation for the blockchain version of AnonRep."""

	def __init__(self, server_host, server_port):
		self.contract_address = sendrecv(
			config.COORDINATOR_ADDR, [Constants.GET_CONTRACT_ADDRESS])
		self.wallets = []
		self.listening = False

		self.respond = {
			Constants.PARTICIPATION_STATUS: self.give_keys,
			Constants.KEYS: self.get_keys,
		}

		self.msg_types = {
			Constants.PARTICIPATION_STATUS: [int],
			Constants.KEYS: [list, list],
		}

		assert set(self.respond.keys()) == set(self.msg_types.keys())

		super().__init__(server_host, server_port)


	def lrs_sign(self, msg):
		"""Sign for LRS."""
		ltp_array = sendrecv(self.server_addr, [Constants.GET_LTP_ARRAY])
		ltp_idx = ltp_array.index(self.pub_key)

		# modify stp_array to prevent duplicate voting
		ltp_array.append(msg_hash(msg, sha1))

		return lrs.sign(msg, self.pri_key, ltp_idx, ltp_array)

	def encrypt(self, payload, rsa_key):
		"""Encrypt a payload using a hybrid cryptosystem.

		Generates a random AES key and uses it to encrypt the payload. Then,
		encrypts the AES key using RSA (PKCS#1 OAEP) with rsa_key.

		Returns a payload with the RSA-encrypted AES key, AES nonce, AES tag, and
		AES-encrpyted payload.
		"""
		aes_key = get_random_bytes(Constants.AES_KEY_LENGTH)

		cipher = AES.new(aes_key, AES.MODE_EAX)  # nonce length 16
		enc_payload, tag = cipher.encrypt_and_digest(payload)  # tag length 16
		enc_aes_key = rsa_key.encrypt(aes_key)  # length 256
		return enc_aes_key + cipher.nonce + tag + enc_payload

	def decrypt(self, payload):
		"""Decrypts a paylod using a hybrid cryptosystem.

		Does the reverse of encrypt(). Decrypts the prepended AES key, then uses
		this AES key, the nonce, and the tag to decrypt the payload.

		Returns the decrypted payload.
		"""
		bytes_in = io.BytesIO(payload)

		enc_aes_key, nonce, tag, enc_payload = [bytes_in.read(x) for x in
			[Constants.RSA_KEY_LENGTH // 8,
			Constants.AES_KEY_LENGTH, Constants.AES_KEY_LENGTH, -1]]

		# first Constants.RSA_KEY_LENGTH bits are the AES key
		aes_key = self.cipher.decrypt(enc_aes_key)

		# decrypt the apyload with the AES key
		aes = AES.new(aes_key, AES.MODE_EAX, nonce)
		dec_payload = aes.decrypt_and_verify(enc_payload, tag)

		return dec_payload

	def get_keys(self, s, msg_args):
		"""Handles receiving keys and next hop addresses from the coordinator."""
		next_addr, e_keys = msg_args
		self.next_addr = tuple(next_addr)
		self.e_keys = [PKCS1_OAEP.new(RSA.importKey(key)) for key in e_keys]
		send(s, ['ACK'])
		s, addr = self.ss.accept()
		self.shuffle(recvbytes(s))

	def give_keys(self, s, msg_args):
		"""Handles a request to give an RS"""
		balance, = msg_args
		# generate wallets
		if balance == 0:
			return
		self.new_wallets = [bc.generate_keypair() for _ in range(balance)]
		# generate RSA key
		self.rsa_keys = RSA.generate(Constants.RSA_KEY_LENGTH)
		self.cipher = PKCS1_OAEP.new(self.rsa_keys)
		# send the RSA key
		send(s, self.rsa_keys.publickey().exportKey().decode(Constants.ENCODING))

	def shuffle(self, payload):
		"""Shuffles a list of keys and adds own key as described in CoinShuffle."""
		if len(payload) == 0:  # first client in the ring
			deserialized = []
		else:
			ciphertext_size = int.from_bytes(
				payload[:Constants.INTEGER_SIZE], byteorder='big')
			assert((len(payload) - Constants.INTEGER_SIZE) % ciphertext_size == 0)
			deserialized = [payload[i:i + ciphertext_size] for i in range(
				Constants.INTEGER_SIZE, len(payload), ciphertext_size)]

		# decrypt each message in the list
		ciphertexts = [self.decrypt(ciphertext) for ciphertext in deserialized]

		# create layered encryption of public keys and add to list
		for wallet in self.new_wallets:
			cur = bytes(wallet.address, encoding=Constants.ENCODING)
			for key in self.e_keys:
				cur = self.encrypt(cur, key)
			ciphertexts.append(cur)

		# shuffle
		random.shuffle(ciphertexts)

		# if this client is the last one in the ring
		if len(self.e_keys) == 0:
			send(self.next_addr, [Constants.SHUFFLE,
				[ct.decode(Constants.ENCODING) for ct in ciphertexts]])
		else:
			sendbytes(self.next_addr, len(ciphertexts[0]).to_bytes(
				Constants.INTEGER_SIZE, byteorder='big') + b''.join(ciphertexts))

		self.wallets = self.new_wallets

	def verify_message(self, msg):
		"""Verifies that the incoming message is valid."""
		if len(msg) == 0:
			return False

		msg_head, *msg_args = msg

		# verify that msg_head is in respond dict
		ret = (msg_head in self.respond)

		# verify that msg_args length matches expected
		ret = ret and (len(msg_args) == len(self.msg_types[msg_head]))

		# verify that all arguments are of the appropriate type
		for i in range(len(msg_args)):
			ret = ret and isinstance(msg_args[i], self.msg_types[msg_head][i])

		return ret

	def start_server(self, ss):
		while True:
			try:
				# accept and receive socket message
				s, addr = ss.accept()
				msg = recv(s)

				# verify message information
				if not self.verify_message(msg):
					eprint(self.name, 'Error processing message.')
					continue

				msg_head, *msg_args = msg

				# respond to received message
				if msg_head in Constants.OPEN_SOCKET:
					self.respond[msg_head](s, msg_args)
				else:
					self.respond[msg_head](msg_args)
				if msg_head == Constants.SHUFFLE:
					break
			except ConnectionAbortedError:
				print()
				ss.close()
				break
			except Exception:
				traceback.print_exc()
		ss.close()
		self.listening = False

	def get_total_reputation(self):
		"""Returns the total reputation."""

	def post(self, msg, rep):
		"""Post a message."""

		# see if wallets have enough reputation
		if len(self.wallets) < rep:
			eprint(self.name, 'You do not have enough reputation to post that.')
			return False

		# if rep is 0, generate a new wallet to use
		if rep == 0:
			wallets_to_use = [bc.generate_keypair()]
		# otherwise, use the first rep wallets in self.wallets
		else:
			wallets_to_use, self.wallets = self.wallets[:rep], self.wallets[rep:]

		# sign public keys
		addresses = [w.address for w in wallets_to_use]
		signatures = [bc.sign(w.privateKey, w.address).signature.hex()
			for w in wallets_to_use]

		# if haven't already, start up a server for coinshuffle.
		if not self.listening:
			self.ss = socket.socket()
			self.ss.bind(config.CLIENT_ADDR)
			self.ss.listen(5)

			self.addr = self.ss.getsockname()
			self.listening = True
			Thread(target=self.start_server, args=(self.ss,), daemon=True).start()

		send(self.server_addr,
			[Constants.NEW_MESSAGE, msg, addresses, signatures, self.addr])

		return True

	def show_help(self):
		"""Display help text."""
		print('Instructions:')
		print('--------------------------------------------------------')
		print('HELP           : Displays this help message')
		print('SHOW           : Shows message')
		print('WRITE [rep]    : Write a message with reputation [rep]')
		print('VOTE UP [num]  : Votes up the message with ID [num]')
		print('VOTE DOWN [num]: Votes down the message with ID [num]')
		print('GET REP        : Displays your reputation')
		print('--------------------------------------------------------')


if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('USAGE: python client_blockchain.py server_host server_port')
		sys.exit(1)

	client_host = sys.argv[1]
	client_port = int(sys.argv[2])
	c = BlockchainClient(client_host, client_port)
	c.show_help()

	while True:
		try:
			s = input('> ').strip().upper()
			if s == 'HELP':
				c.show_help()
			elif s == 'SHOW':
				messages = sendrecv(config.COORDINATOR_ADDR, [Constants.DISP_BOARD])
				pprint.PrettyPrinter(indent=4).pprint(messages)
			elif s == 'GET REP':
				print('Your reputation is: {}'.format(
					sum(c.blockchain.get_reputation(x.address) for x in c.wallets)))
			elif re.match("^WRITE \d+$", s) is not None:
				msg = input('Write message here: ')
				c.post(msg, int(s.split()[-1]))
				pass
			elif re.match("^VOTE UP \d+$", s) is not None:
				c.vote(1, int(s.split()[-1]))
				pass
			elif re.match("^VOTE DOWN \d+$", s) is not None:
				c.vote(-1, int(s.split()[-1]))
				pass
			else:
				print('Invalid command. Type in HELP for instructions.')
		except KeyboardInterrupt:
			print()
			break
