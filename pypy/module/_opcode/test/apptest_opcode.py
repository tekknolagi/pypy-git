import pytest

import opcode

def test_errors():
    pytest.raises(ValueError, opcode.stack_effect, opcode.opmap["LOAD_CONST"])
    pytest.raises(ValueError, opcode.stack_effect, opcode.opmap["BINARY_ADD"], 1)
    pytest.raises(ValueError, opcode.stack_effect, 1231231)
    pytest.raises(ValueError, opcode.stack_effect, opcode.opmap["EXTENDED_ARG"])

def test_call_function():
    assert opcode.stack_effect(opcode.opmap["CALL_FUNCTION"], 3) == -3
    assert opcode.stack_effect(opcode.opmap["EXTENDED_ARG"], 3) == 0

def test_invalid_opcode():
    pytest.raises(ValueError, opcode.stack_effect, 0)
    pytest.raises(ValueError, opcode.stack_effect, 0, 0)

def test_jump():
    assert opcode.stack_effect(opcode.opmap["FOR_ITER"], 0, jump=True) == -1
    assert opcode.stack_effect(opcode.opmap["FOR_ITER"], 0, jump=False) == 1
    assert opcode.stack_effect(opcode.opmap["FOR_ITER"], 0) == 1

def test_conditional_jump():
    assert opcode.stack_effect(opcode.opmap["JUMP_IF_TRUE_OR_POP"], 0, jump=True) == 0
    assert opcode.stack_effect(opcode.opmap["JUMP_IF_TRUE_OR_POP"], 0, jump=False) == -1
