# anonrep

## Setup
1. (Optional) Start a virtualenv
2. `pip install -r requirements.txt`
3. `brew tap ethereum/ethereum && brew install ethereum`
4. `brew install solidity`
5. `npm install -g npm ganache-cli`

## Usage (not at all final, just for developers' reference)
To start up a test blockchain with auto-mining and virtually unlimited resources, run:
```
ganache-cli -a 1 -g 1
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

## Testing
Run `pytest` to run tests.

