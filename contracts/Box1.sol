//SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

contract Box1 {
    uint256 value;

    function setVal(uint256 _value) public {
        value = _value;
    }

    function getVal() public view returns (uint256) {
        return value;
    }
}
