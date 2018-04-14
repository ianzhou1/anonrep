# anonrep

## Setup (TODO organize this)
- pip install the requirements.txt
- brew tap ethereum/ethereum
- brew install ethereum
- brew install solidity
- npm install -g npm ganache-cli

## Usage (not at all final, just for developers' reference)
To start up a test blockchain with auto-mining and virtually unlimited resources, run:
```
ganache-cli -a 1 -g 1 -l 9999999999 -e 9999999999
```

First, start up a coordinator:
```
python src/coordinator.py
```

Then, start up the normal servers:
```
python src/server.py [server_host] [server_port]
```

Then, start up clients:
```
python src/client.py [server_host] [server_port]
```

