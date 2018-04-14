import pytest
import blockchain as bc

def test_blockchain():
	coordinator = bc.LocalBlockchain()
	client = bc.LocalBlockchain()

	addr = coordinator.deploy_contract('reputation.sol')
	client.connect_to_contract('reputation.sol', addr)

	account1 = bc.generate_keypair()

	assert coordinator.get_balance(account1) == 0

	coordinator.add_reputation(account1.address, 69)
	assert client.get_balance(account1) == 69

	coordinator.remove_reputation(account1.address, 68)
	assert client.get_balance(account1) == 1

	# reputation cannot go negative
	with pytest.raises(ValueError):
		coordinator.remove_reputation(account1.address, 500)

	test_message = 'TEST MESSAGE'
	x = bc.sign(account1, test_message)
	assert bc.verify(account1.address, test_message, x.signature)
