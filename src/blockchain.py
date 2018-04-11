import os

from web3 import Web3, HTTPProvider
from solc import compile_files

class GanacheBlockchain:
	def __init__(self, endpoint_uri=None):
		if endpoint_uri is None:
			self.w3 = Web3()
		else:
			self.w3 = Web3(HTTPProvider(endpoint_uri))

	def _compile_contract(file_name):
		(_, contract_interface), = compile_files(
			[os.path.join(os.path.dirname(os.path.realpath(__file__)), file_name)]).items()
		return contract_interface

	# Assumes one contract is defined per file and that the file lies in the same directory as this file.
	def deploy_contract(self, file_name):
		contract_interface = GanacheBlockchain._compile_contract(file_name)
		contract = self.w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
		tx_hash = contract.constructor().transact(transaction={'from': self.w3.eth.accounts[0], 'gas': 10 ** 6})
		tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)
		contract_address = tx_receipt['contractAddress']
		self.contract_instance = self.w3.eth.contract(abi=contract_interface['abi'], address=contract_address)
		return contract_address

	# Assumes one contract is defined per file and that the file lies in the same directory as this file.
	def connect_to_contract(self, file_name, contract_address):
		contract_interface = GanacheBlockchain._compile_contract(file_name)
		self.contract_instance = self.w3.eth.contract(abi=contract_interface['abi'], address=contract_address)
