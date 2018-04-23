from testing_helpers import *
from util import Constants
import random

def test_base_anonrep():
	co = create_coordinator()
	s1 = create_server()
	s2 = create_server()

	begin_client_registration(co)

	c1 = create_client(s1)
	c2 = create_client(s1)

	start_message_phase(co)

	post(c1, 'hello1')
	post(c2, 'hello2')

	start_feedback_phase(co)

	board_before_voting = c1.get_message_board()
	assert(len(board_before_voting) == 2)

	vote(c1, -1, 0)
	vote(c1, -1, 0)
	vote(c1, 1, 1)
	vote(c2, 1, 0)

	board_after_voting = c2.get_message_board()
	assert(len(board_after_voting) == 2)
	# make sure the duplicate vote wasn't counted but the other votes were
	assert(board_after_voting[0][1][Constants.FB] == [1, -1])
	assert(board_after_voting[1][1][Constants.FB] == [1, 0])

	end_round(co)
