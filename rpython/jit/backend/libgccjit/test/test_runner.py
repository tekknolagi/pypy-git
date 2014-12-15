import py
from rpython.jit.backend.detect_cpu import getcpuclass
from rpython.jit.backend.test.runner_test import LLtypeBackendTest,\
     boxfloat, constfloat
from rpython.jit.metainterp.history import (BasicFailDescr, BasicFinalDescr,
                                            BoxInt)
from rpython.jit.metainterp.resoperation import ResOperation, rop
from rpython.jit.tool.oparser import parse
from rpython.rtyper.lltypesystem import lltype, llmemory
from rpython.rtyper import rclass
from rpython.rtyper.annlowlevel import llhelper
from rpython.jit.codewriter.effectinfo import EffectInfo
from rpython.jit.metainterp.history import JitCellToken, TargetToken
from rpython.jit.codewriter import longlong


CPU = getcpuclass()

class FakeStats(object):
    pass


class TestLibGccjit(LLtypeBackendTest):

    # for the individual tests see
    # ====> ../../test/runner_test.py

    def get_cpu(self):
        cpu = CPU(rtyper=None, stats=FakeStats())
        cpu.setup_once()
        return cpu
