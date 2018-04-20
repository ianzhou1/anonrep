from testing_helpers import *

def test_basic_coinshuffle():
	co = create_blockchain_coordinator()
	s = create_blockchain_server()

	begin_client_registration(co)

	c1 = create_blockchain_client(s)
	c2 = create_blockchain_client(s)
	c3 = create_blockchain_client(s)

	start_message_phase(co)

	post_blockchain(c1, 'hello1', 0)
	post_blockchain(c2, 'hello2', 0)
	post_blockchain(c3, 'hello3', 0)

	start_feedback_phase(co)

	original_addresses = [c.wallets[0].address for c in [c1, c2, c3]]

	vote(c1, 1, 0)
	vote(c1, 1, 1)
	vote(c1, 1, 2)

	start_coinshuffle_phase(co)

	new_addresses = [c.wallets[0].address for c in [c1, c2, c3]]

	assert(len(set(original_addresses) & set(new_addresses)) == 0)