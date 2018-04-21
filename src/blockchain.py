import os
import time

from web3 import Web3, HTTPProvider
from web3.auto import w3
from web3.contract import ConciseContract
from solc import compile_files

w3.eth.enable_unaudited_features()


def generate_keypair():
	"""Generates a public/private key pair for use in the blockchain."""
	return w3.eth.account.create()


def sign(private_key, msg):
	"""Signs a message with a private key generated from generate_keypair()."""
	return w3.eth.account.sign(message_text=msg, private_key=private_key)


def verify(addr, msg, signature):
	"""Verifies that an address of addr signed msg to produce signature."""
	return w3.eth.account.recoverMessage(text=msg, signature=signature) == addr


def _compile_contract(file_name):
	(_, contract_interface), = compile_files([os.path.join(
		os.path.dirname(os.path.realpath(__file__)), file_name)]).items()
	return contract_interface


class LocalBlockchain:
	"""Interface to a local blockchain provider like Ganache/Geth/testrpc."""

	def __init__(self, endpoint_uri=None):
		"""Connects to a provider at endpoint_uri."""
		if endpoint_uri is None:
			self.w3 = Web3()
		else:
			self.w3 = Web3(HTTPProvider(endpoint_uri))
		if not any(provider.isConnected() for provider in self.w3.providers):
			raise Exception('Could not connect to any provider!')
		self.contract_instance = None

	def deploy_contract(self, file_name):
		"""Deploys contract located at file_name.

		This method assumes that file_name only contains one contract and that the
		contract file lies in the same directory as this source file.
		"""
		contract_interface = _compile_contract(file_name)
		contract = self.w3.eth.contract(
			abi=contract_interface['abi'], bytecode=contract_interface['bin'])
		tx_hash = contract.constructor().transact(
			transaction={'from': self.w3.eth.accounts[0], 'gas': 10 ** 6})
		while self.w3.eth.getTransactionReceipt(tx_hash) is None:
			time.sleep(0.01)
		tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)
		contract_address = tx_receipt['contractAddress']
		self.contract_instance = self.w3.eth.contract(
			abi=contract_interface['abi'],
			address=contract_address,
			ContractFactoryClass=ConciseContract)
		self.transaction = {'from': self.w3.eth.accounts[0], 'gas': 100000}
		return contract_address

	def connect_to_contract(self, file_name, contract_address):
		"""Connects to contract defined in file_name and deployed to
		contract_address.

		This method assumes that file_name only contains one contract and that the
		contract file lies in the same directory as this source file.
		"""
		contract_interface = _compile_contract(file_name)
		self.contract_instance = self.w3.eth.contract(
			abi=contract_interface['abi'],
			address=contract_address,
			ContractFactoryClass=ConciseContract)

	def get_reputation(self, address):
		"""Gets the reputation of address."""
		if self.contract_instance is None:
			print('Error: Call deploy_contract or connect_to_contract first.')
		return self.contract_instance.getBalance(address)

	def add_reputation(self, addr, rep):
		"""Adds rep reputation to addr."""
		if self.contract_instance is None:
			print('Error: Call deploy_contract or connect_to_contract first.')
		return Promise(self.w3, self.contract_instance.addReputation(
			addr, rep, transact=self.transaction))

	def remove_reputation(self, addr, rep):
		"""Removes rep reputation from addr."""
		if self.contract_instance is None:
			print('Error: Call deploy_contract or connect_to_contract first.')
		return Promise(self.w3, self.contract_instance.removeReputation(
			addr, rep, transact=self.transaction))

	def transfer(self, sender, receiver):
		"""Transfers one reputation from sender to receiver."""
		if self.contract_instance is None:
			print('Error: Call deploy_contract or connect_to_contract first.')
		return Promise(self.w3, self.contract_instance.transfer(
			sender, receiver, transact=self.transaction))

class Promise:
	"""Contains a possibly unfinished transaction."""
	def __init__(self, w3, tx_hash):
		self.tx_hash = tx_hash
		self.w3 = w3

	def resolve(self, sleep=0.001):
		"""Waits for the transaction to be mined."""
		while self.w3.eth.getTransactionReceipt(self.tx_hash) is None:
			time.sleep(sleep)
