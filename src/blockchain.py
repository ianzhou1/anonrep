import os
import time

from web3 import Web3, HTTPProvider
from web3.auto import w3
from web3.contract import ConciseContract
from solc import compile_files

w3.eth.enable_unaudited_features()

def _compile_contract(file_name):
	(_, contract_interface), = compile_files(
		[os.path.join(os.path.dirname(os.path.realpath(__file__)), file_name)]).items()
	return contract_interface

def generate_keypair():
	return w3.eth.account.create()

def sign(account, msg):
	return w3.eth.account.sign(message_text=msg, private_key=account.privateKey)

def verify(addr, msg, signature):
	return w3.eth.account.recoverMessage(text=msg, signature=signature) == addr

class LocalBlockchain:
	def __init__(self, endpoint_uri=None, etp=None):
		if endpoint_uri is None:
			self.w3 = Web3()
		else:
			self.w3 = Web3(HTTPProvider(endpoint_uri))
		if not any(provider.isConnected() for provider in self.w3.providers):
			raise Exception('Could not connect to any provider!')
		self.contract_instance = None

	# Assumes one contract is defined per file and that the file lies in the same directory as this file.
	def deploy_contract(self, file_name):
		contract_interface = _compile_contract(file_name)
		contract = self.w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'], )
		tx_hash = contract.constructor().transact(transaction={'from': self.w3.eth.accounts[0], 'gas': 10 ** 6})
		while self.w3.eth.getTransactionReceipt(tx_hash) is None:
			time.sleep(0.1)
		tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)
		contract_address = tx_receipt['contractAddress']
		self.contract_instance = self.w3.eth.contract(
			abi=contract_interface['abi'],
			address=contract_address,
			ContractFactoryClass=ConciseContract)
		self.transaction = {'from': self.w3.eth.accounts[0], 'gas': 100000}
		return contract_address

	# Assumes one contract is defined per file and that the file lies in the same directory as this file.
	def connect_to_contract(self, file_name, contract_address):
		contract_interface = _compile_contract(file_name)
		self.contract_instance = self.w3.eth.contract(
			abi=contract_interface['abi'],
			address=contract_address,
			ContractFactoryClass=ConciseContract)

	def get_balance(self, address):
		if self.contract_instance is None:
			print('Error: Call deploy_contract or connect_to_contract first.')
		return self.contract_instance.getBalance(address)

	def add_reputation(self, addr, rep):
		if self.contract_instance is None:
			print('Error: Call deploy_contract or connect_to_contract first.')
		self.contract_instance.addReputation(addr, rep, transact=self.transaction)

	def remove_reputation(self, addr, rep):
		if self.contract_instance is None:
			print('Error: Call deploy_contract or connect_to_contract first.')
		self.contract_instance.removeReputation(addr, rep, transact=self.transaction)

	def transfer(self, sender, receiver):
		if self.contract_instance is None:
			print('Error: Call deploy_contract or connect_to_contract first.')
		self.contract_instance.transfer(sender, receiver, transact=self.transaction)
