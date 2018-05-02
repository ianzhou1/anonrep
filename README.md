# anonrep (TODO: Think of name for the new system)

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

## Example

TODO: We will make this similar to the AnonCred "[A simple demo](https://github.com/anonyreputation/anonCred#a-simple-demo)" section.

## Testing
Run `pytest` to run tests.

