import sys
import time
from threading import Thread

import blockchain as bc
import config

from board_blockchain import BlockchainMessageBoard
from coordinator import Coordinator
from util import Constants, send

class BlockchainCoordinator(Coordinator):
    def __init__(self, host, port):
        self.blockchain = bc.LocalBlockchain()
        self.contract_address = self.blockchain.deploy_contract('reputation.sol')
        super().__init__(host, port)

        self.board = BlockchainMessageBoard(self)

        # add items to self.respond and self.msg_types
        new_respond = {
            Constants.GET_CONTRACT_ADDRESS: self.get_contract_address
        }

        new_msg_types = {
            Constants.GET_CONTRACT_ADDRESS: []
        }

        assert set(new_respond.keys()) == set(new_msg_types.keys())

        self.respond.update(new_respond)
        self.msg_types.update(new_msg_types)

    def get_contract_address(self, s, msg_args):
        send(s, self.contract_address)


if __name__ == '__main__':
    if len(sys.argv) != 1:
        print('USAGE: python coordinator.py')
        sys.exit(1)

    print('*** Press [ENTER] to begin client registration. ***')
    c = BlockchainCoordinator(config.COORDINATOR_SERVER, config.COORDINATOR_PORT)
    try:
        thread = Thread(target=c.run)
        thread.start()

        input()
        c.begin_client_registration()

        print('*** Press [ENTER] to begin announcement phase. ***')
        input()
        c.phase = Constants.ANNOUNCEMENT_PHASE

        while True:
            c.begin_announcement_phase()
            while c.phase != Constants.MESSAGE_PHASE:
                time.sleep(0.1)
            # message phase has begun
            c.board.begin_message_phase()
            time.sleep(Constants.MESSAGE_PHASE_LENGTH_IN_SECS)
            c.sprint('Beginning feedback phase...')
            c.phase = Constants.FEEDBACK_PHASE
            time.sleep(Constants.FEEDBACK_PHASE_LENGTH_IN_SECS)
            c.phase = Constants.VOTE_CALCULATION_PHASE
            c.board.end_feedback_phase()
            c.end_round()
            while c.phase == Constants.FEEDBACK_PHASE:
                time.sleep(0.1)
    finally:
        c.ss.close()
