pragma solidity ^0.4.0;

contract Reputation {
    address public owner;
    mapping (address => uint) public balances;

    event AddReputation(address _addr, uint _rep);
    event RemoveReputation(address _addr, uint _rep);
    event Transfer(address _from, address _to);

    function Reputation() public {
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
        require(_addr != 0x0);
        _;
    }

    function transferOwnership(address _newOwner) public onlyOwner {
        require(_newOwner != address(0));
        owner = _newOwner;
    }

    /*
     * REPUTATION FUNCTIONS
     */

    function getBalance(address _addr) public view returns (uint) {
        return balances[_addr];
    }

    function addReputation(address _addr, uint _rep) public onlyOwner {
        uint overflowCheck = balances[_addr];
        balances[_addr] += _rep;
        // check for overflow
        assert(balances[_addr] >= overflowCheck);
        emit AddReputation(_addr, _rep);
    }

    function removeReputation(address _addr, uint _rep) public onlyOwner addressValid(_addr) {
        require(balances[_addr] >= _rep);
        balances[_addr] -= _rep;
        emit RemoveReputation(_addr, _rep);
    }

    function transfer(address _from, address _to) public onlyOwner addressValid(_from) addressValid(_to) {
        require(getBalance(_from) > 0);
        require(getBalance(_to) == 0);

        balances[_from] -= 1;
        balances[_to] += 1;
        emit Transfer(_from, _to);
    }
}
