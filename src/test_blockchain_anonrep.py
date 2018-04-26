from testing_helpers import *
from util import Constants
from itertools import chain

def test_announcement_phase():
	anonrep = LocalBlockchainAnonRep(2, [1, 1])
	s1, s2 = anonrep.servers
	c1, c2 = anonrep.clients

	anonrep.start_message_phase()

	# make sure the servers have the same ltp/stp lists
	assert(s1.stp_list == s2.stp_list)
	assert(s1.ltp_list == s2.ltp_list)

	# make sure all the ltp's are in there
	assert(set([c1.pub_key, c2.pub_key]) == s1.ltp_list.keys())

	# make sure the ltp's are encrypted
	assert(s1.ltp_list.keys() != s1.stp_list.keys())
	assert(len(s1.ltp_list.keys()) == 2)

	# make sure the scores are encrypted in ltp_list
	assert(set(s1.ltp_list.values()) != set([1]))
	assert(set(s1.stp_list.values()) == set([1]))

	old_ltp_list = dict(s1.ltp_list)
	old_stp_list = dict(s1.stp_list)

	anonrep.start_feedback_phase()
	anonrep.end_round()
	anonrep.start_message_phase()

	# make sure the stp reputations change but not the ltp's
	assert(old_stp_list.values() != s1.stp_list.values())
	assert(old_ltp_list.keys() == s1.ltp_list.keys())


def test_message_and_feedback_phase():
	anonrep = LocalBlockchainAnonRep(2, [1, 1])
	s1, s2 = anonrep.servers
	c1, c2 = anonrep.clients

	anonrep.start_message_phase()

	anonrep.post(0, 'hello1', 0)
	anonrep.post(1, 'hello2', 0)

	anonrep.start_feedback_phase()

	board_before_voting = c1.get_message_board()
	assert(len(board_before_voting) == 2)

	anonrep.vote(0, -1, 0)
	anonrep.vote(0, -1, 0)
	anonrep.vote(1, 1, 1)
	anonrep.vote(1, 1, 0)

	board_after_voting = c2.get_message_board()
	assert(len(board_after_voting) == 2)
	# make sure the duplicate vote wasn't counted but the other votes were
	assert(board_after_voting[0][1][Constants.FB] == [1, -1])
	assert(board_after_voting[1][1][Constants.FB] == [1, 0])

	anonrep.end_round()


def test_basic_coinshuffle():
	anonrep = LocalBlockchainAnonRep(1, [3])
	s1, = anonrep.servers
	c1, c2, c3 = anonrep.clients

	anonrep.start_message_phase()

	anonrep.post(0, 'hello0', 0)
	anonrep.post(1, 'hello1', 0)
	anonrep.post(2, 'hello2', 0)

	# this message should not go through because c1 does not have enough rep
	anonrep.post(0, 'hello1', 1)

	anonrep.start_feedback_phase()

	addrs = [post[1][Constants.REP][0] for post in anonrep.co.board.board]

	assert(len(addrs) == 3)

	anonrep.vote(0, 1, 0)
	anonrep.vote(0, 1, 1)
	anonrep.vote(0, 1, 2)
	anonrep.vote(1, 1, 0)
	anonrep.vote(2, 1, 0)

	# this duplicate vote should not be counted
	anonrep.vote(0, 1, 0)

	anonrep.start_coinshuffle_phase()
	anonrep.end_round()

	new_addrs = list(chain(*[c.wallets for c in [c1, c2, c3]]))

	assert(len(set(new_addrs)) == len(new_addrs))
	assert(len(set(addrs) & set(new_addrs)) == 0)

	assert(len(c1.wallets) == 3)
	assert(len(c2.wallets) == 1)
	assert(len(c3.wallets) == 1)

	# this new round will have no participants in the CoinShuffle.

	anonrep.start_message_phase()

	anonrep.post(1, 'hello3', 1)

	anonrep.start_feedback_phase()

	anonrep.vote(0, -1, 3)

	anonrep.start_coinshuffle_phase()
	anonrep.end_round()

	assert(len(c2.wallets) == 0)

	# this new round will have only one participant.

	anonrep.start_message_phase()

	anonrep.post(2, 'hello4', 1)
	anonrep.post(0, 'hello5', 3)

	anonrep.start_feedback_phase()

	anonrep.vote(1, -1, 4)

	anonrep.start_coinshuffle_phase()
	anonrep.end_round()

	assert(len(c1.wallets) == 3)
	assert(len(c2.wallets) == 0)
	assert(len(c3.wallets) == 0)
