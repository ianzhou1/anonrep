pragma solidity ^0.4.0;

// contract Greeter {
//     string public greeting;
//     mapping (address => int) public numTokens;

//     function Greeter() {
//         greeting = 'Hello';
//     }

//     function setGreeting(string _greeting) public {
//         greeting = _greeting;
//     }

//     function greet() constant returns (string) {
//         return greeting;
//     }

//     function getAddress() view returns (address) {
//         return msg.sender;
//     }
// }

contract Reputation {
    address public owner;
    mapping (address => bool) public accountActive;
    mapping (address => uint) public balances;

    event CreateWallet(address _addr);
    event AddReputation(address _addr, uint _rep);
    event RemoveReputation(address _addr, uint _rep);
    event Transfer(address _from, address _to);

    function Reputation() {
        owner = msg.sender;
    }

    /*
     * OWNERSHIP FUNCTIONS (Adapted from OpenZeppelin's Ownable contract)
     */

    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }

    modifier addressValid(address _addr) {
        require(accountActive[_addr] = true);
        _;
    }

    function transferOwnership(address _newOwner) public onlyOwner {
        require(_newOwner != address(0));
        owner = _newOwner;
    }

    /*
     * REPUTATION FUNCTIONS
     */

    function getBalance(address _addr) public view {
        return balances[_addr];
    }

    function isActive(address _addr) public view {
        return accountActive[_addr];
    }

    function createWallet(address _addr) public onlyOwner {
        accountActive[_addr] = true;
        CreateWallet(_addr);
    }

    function addReputation(address _addr, uint _rep) public onlyOwner addressValid(_addr) {
        uint overflowCheck = balances[_addr];
        balances[_addr] += _rep;
        // check for overflow
        assert(balances[_addr] >= overflowCheck);
        AddReputation(_addr, _rep);
    }

    function removeReputation(address _addr, uint _rep) public onlyOwner addressValid(_addr) {
        require(balances[_addr] >= _rep);
        balances[_addr] -= _rep;
        RemoveReputation(_addr, _rep);
    }

    function transfer(address _from, address _to) public onlyOwner addressValid(_from) addressValid(_to) {
        require(getBalance(_from) > 0);
        require(getBalance(_to) == 0);

        balances[_from] -= 1;
        balances[_to] += 1;

        Transfer(_from, _to);
    }
}
