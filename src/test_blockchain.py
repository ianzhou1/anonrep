import pytest
import blockchain as bc

def test_blockchain():
	coordinator = bc.LocalBlockchain()
	client = bc.LocalBlockchain()

	addr = coordinator.deploy_contract('reputation.sol')
	client.connect_to_contract('reputation.sol', addr)

	account1 = bc.generate_keypair()

	assert(coordinator.get_reputation(account1.address) == 0)

	coordinator.add_reputation(account1.address, 70)
	assert(client.get_reputation(account1.address) == 70)

	coordinator.remove_reputation(account1.address, 68)
	assert(client.get_reputation(account1.address) == 2)

	# reputation cannot go negative
	with pytest.raises(ValueError):
		coordinator.remove_reputation(account1.address, 500)

	# test signatures
	test_message = 'TEST MESSAGE'
	x = bc.sign(account1.privateKey, test_message)
	assert(bc.verify(account1.address, test_message, x.signature))

	assert(not bc.verify(account1.address, 'nope', x.signature))
