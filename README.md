# AnonRep++

## Overview
This repository contains:
1. A Python implementation of an intersection-attack-resistant improvement of the original [AnonRep](http://www.cs.yale.edu/homes/zhai-ennan/zhai16anonrep.pdf) anonymous reputation system
2. A Python implementation of the original AnonRep system.

The improvement in the new system that it stores users' reputation scores in the Ethereum (or other Solidity-based) blockchain, as opposed to in the AnonRep servers, using CoinShuffle to maintain anonymity. This yields the following benefits:
1. We don't need one-time pseudonyms anymore, so we don't need the announcement phase and verifiable shuffles.
2. Users can post messages with any non-negative reputation that does not exceed their total reputation, which protects against intersection attacks.

## Setup
1. (Optional) Start a virtualenv
2. `pip install -r requirements.txt`
3. Install Ethereum. On a Mac, you can run `brew tap ethereum/ethereum && brew install ethereum`
4. Install Solidity, the language that our smart contract is written in. On a Mac, you can run `brew install solidity`
5. Start an Ethereum node. You can install a local, test node with `npm install -g npm ganache-cli`

## Usage
After cloning this repository, be sure to modify `config.py` to supply the appropriate coordinator/client address and to set the length of the message and feedback phases.

To start up a test blockchain with auto-mining and virtually unlimited resources, run:
```
ganache-cli -a 1 -g 1
```

First, start up a coordinator:
```
python src/coordinator_blockchain.py
```

Then, start up the servers:
```
python src/server_blockchain.py [server_host] [server_port]
```
After all the servers have connected, press the [Enter] key on the coordinator to begin the client registration phase.
Then, start up the clients:
```
python src/client_blockchain.py [server_host] [server_port]
```
Once everything is done, press the [Enter] key on the coordinator again to begin the announcement phase.

### Running the original AnonRep
To run the original AnonRep, follow the same instructions as the section above, except there is no need to start up `ganache-cli`, and run `coordinator.py`, `server.py`, and `client.py` instead of their blockchain counterparts.

## Example Run

In this scenario, we start up:
1. One coordinator on `ladybug.zoo.cs.yale.edu:5557`.
2. Two servers on `aphid.zoo.cs.yale.edu:5557` and `dolphin.zoo.cs.yale.edu:5557`.
3. Two clients, one connected to each server, with their CoinShuffle servers on `ladybug.zoo.cs.yale.edu`. We make the clients on the same host as the coordinator for convenience, so we only need to start one blockchain provider.

Before we do anything, we update `src/config.py` to match this scenario. The file should look like:
```python
# addresses are in (host, port) format
COORDINATOR_ADDR = ('ladybug.zoo.cs.yale.edu', 5557)
CLIENT_ADDR = ('ladybug.zoo.cs.yale.edu', 0)
MESSAGE_PHASE_LENGTH_IN_SECS = 6
FEEDBACK_PHASE_LENGTH_IN_SECS = 6
```

Now, we run `ganache-cli -a 1 -g 1` on `ladybug`. The output should look like
```
-bash-4.4$ ganache-cli -a 1 -g 1
Ganache CLI v6.1.0 (ganache-core: 2.1.0)

Available Accounts
==================
(0) 0x611841ceb05f2cec4fe2c738f9686140894a4ee8

Private Keys
==================
(0) dbaa815d9e31a0dc9baf18a243e4eff1d61f62f7309f07ca767df08053a47f18

HD Wallet
==================
Mnemonic:      topic steak proud right benefit throw ginger gospel practice spy win juice
Base HD Path:  m/44'/60'/0'/0/{account_index}

Gas Price
==================
1

Listening on localhost:8545
```
Then, in another shell connected to `ladybug`, we run `python src/coordinator_blockchain.py`. The screen should look like this:
```
(.virtualenv) -bash-4.4$ python src/coordinator_blockchain.py
*** Press [ENTER] to begin message phase. ***
# servers: 0 | []
```
Next, on `aphid` and `dolphin` we run `python src/server_blockchain.py aphid.zoo.cs.yale.edu 5557` and `python src/server_blockchain.py aphid.zoo.cs.yale.edu 5557`, respectively. The screens should look like this:
```
(.virtualenv) -bash-4.4$ python src/server_blockchain.py aphid.zoo.cs.yale.edu 5557
[SERVER] Server id: 0
```
```
(.virtualenv) -bash-4.4$ python src/server_blockchain.py dolphin.zoo.cs.yale.edu 5557
[SERVER] Server id: 1
```
In base AnonRep, we would have to press the enter/return key in the coordinator shell to begin client registration phase. But here, we can go straight to registering the clients. To register the clients, in two `ladybug` terminals we run `python src/client_blockchain.py aphid.zoo.cs.yale.edu 5557` and `python src/client_blockchain.py dolphin.zoo.cs.yale.edu 5557`. The screen should look something like this:
```
(.virtualenv) -bash-4.4$ python src/client_blockchain.py aphid.zoo.cs.yale.edu 5557
Instructions:
--------------------------------------------------------
HELP           : Displays this help message
SHOW           : Shows message
WRITE [rep]    : Write a message with reputation [rep]
VOTE UP [num]  : Votes up the message with ID [num]
VOTE DOWN [num]: Votes down the message with ID [num]
GET REP        : Displays your reputation
--------------------------------------------------------
>
```
Now that the coordinator, servers, and clients are set up, we can press the enter/return key in the coordinator shell to begin the message phase. Now we can write a message in the client by entering `WRITE 0` in the shell, then the message.
```
> WRITE 0
Write message here: Hello there!
>
```
Once the coordinator says it is feedback phase, we can vote on a message. On the other client, we can write `SHOW` to show the message board then `VOTE UP 0` to vote up the first message in the message board. The `fb` field denotes the number of upvotes and downvotes. the `rep` field is an array of the wallet public keys used to post the message.
```
> SHOW
[   [   0,
        {   'fb': [0, 0],
            'msg': 'Hello there!',
            'rep': ['0x2907285771a7afC4cf250A3D13358054f63AFc90']}]]
> VOTE UP 0
>
```
After the CoinShuffle phase finishes, we can enter `GET REP` in the first client to see that its reputation is now one. We can also enter `SHOW` to see the message board and the one vote that has been cast.
```
> GET REP
Your reputation is: 1
> SHOW
[   [   0,
        {   'fb': [1, 0],
            'msg': 'Hello there!',
            'rep': ['0x2907285771a7afC4cf250A3D13358054f63AFc90']}]]
>
```

## Testing
Run `pytest` to run tests.

