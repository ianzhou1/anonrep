from testing_helpers import *
from util import Constants


def test_announcement_phase():
	anonrep = LocalBaseAnonRep(2, [2, 1])
	s1, s2 = anonrep.servers
	c1, c2, c3 = anonrep.clients

	anonrep.start_message_phase()

	# make sure the servers have the same ltp/stp lists
	assert(s1.stp_list == s2.stp_list)
	assert(s1.ltp_list == s2.ltp_list)

	# make sure all the ltp's are in there
	assert(set([c1.pub_key, c2.pub_key, c3.pub_key]) == s1.ltp_list.keys())

	# make sure the ltp's are encrypted
	assert(s1.ltp_list.keys() != s1.stp_list.keys())
	assert(len(s1.ltp_list.keys()) == 3)

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
	anonrep = LocalBaseAnonRep(2, [2, 1])
	s1, s2 = anonrep.servers
	c1, c2, c3 = anonrep.clients

	anonrep.start_message_phase()

	anonrep.post(0, 'hello1')
	anonrep.post(1, 'hello2')

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
