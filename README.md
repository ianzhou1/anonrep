# anonrep

## Setup (TODO organize this)
- pip install the requirements.txt
- brew tap ethereum/ethereum
- brew install ethereum
- brew install solidity

## Usage (not at all final, just for developers' reference)
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

