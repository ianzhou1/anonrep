from testing_helpers import *
import random
import time

def test_base_anonrep():
	co = create_coordinator()
	p = random.sample(range(1000, 65536), 2)
	s1 = create_server(p[0])
	s2 = create_server(p[1])

	begin_client_registration(co)

	c1 = create_client(s1)
	c2 = create_client(s1)

	start_message_phase(co)

	post(c1, 'hello1')
	post(c2, 'hello2')

	start_feedback_phase(co)

	show(c1)

	vote(c1, -1, 0)
	vote(c1, -1, 0)
	vote(c1, 1, 1)
	vote(c2, 1, 0)

	show(c2)

	end_round(co)

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

	original_addresses = [post[1][Constants.REP][0] for post in co.board.board]

	vote(c1, 1, 0)
	vote(c1, 1, 1)
	vote(c1, 1, 2)

	start_coinshuffle_phase(co)

	new_addresses = [c.wallets[0].address for c in [c1, c2, c3]]

	assert(len(set(original_addresses) & set(new_addresses)) == 0)


"""TO TEST:

- Consecutive Coinshuffles for
	- People going from 0 reputation -> nonzero reputation
	- People going from nonzero reputation -> zero reputation


"""