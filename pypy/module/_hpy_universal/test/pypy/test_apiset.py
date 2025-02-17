import pytest
import operator
from rpython.rtyper.lltypesystem import lltype
from pypy.module._hpy_universal import llapi
from pypy.module._hpy_universal.apiset import APISet

class TestAPISet(object):

    @pytest.fixture
    def api(self):
        return APISet(llapi.cts, mode="universal")

    def test_parse_signature(self, api):
        sig = 'HPy HPyNumber_Add(HPyContext *ctx, HPy x, HPy y)'
        name, FUNC, ll_errval = api.parse_signature(sig, error_value=None)
        assert name == 'HPyNumber_Add'
        assert FUNC.TO.ARGS == (llapi.HPyContext, llapi.HPy, llapi.HPy)
        assert FUNC.TO.RESULT == llapi.HPy
        assert ll_errval == 0

    def test_func(self, api):
        @api.func('double divide(long a, long b)', error_value=-1.0)
        def divide(space, a, b):
            return float(a)/b
        #
        assert divide(None, 5, 2) == 2.5
        assert api.all_functions == [divide]

    def test_func_with_func_name(self, api):
        def make_binary(name, op):
            @api.func('double func(long a, long b)', func_name=name, error_value=-1.0)
            def func(space, a, b):
                return op(a, b)
            return func
        #
        add = make_binary('add', operator.add)
        sub = make_binary('sub', operator.sub)
        assert add.__name__ == 'add'
        assert sub.__name__ == 'sub'
        assert add(None, 8, 5) == 13
        assert sub(None, 12, 3) == 9
        assert api.all_functions == [add, sub]

    def test_basename(self, api):
        @api.func('void HPyFoo_Bar(void)')
        def HPyFoo_Bar(space):
            return None
        @api.func('void _HPyFoo_Internal(void)')
        def _HPyFoo_Internal(space):
            return None

        assert HPyFoo_Bar.basename == 'Foo_Bar'
        assert _HPyFoo_Internal.basename == 'Foo_Internal'

    def test_llhelper(self, api):
        class FakeState:
            def get_handle_manager(self, *args):
                return 'fake manager'

        class FakeSpace:
            @staticmethod
            def fromcache(cls):
                return FakeState()

        @api.func('double divide(double a, double b)', error_value=-1.0)
        def divide(space, handles, a, b):
            assert space is fakespace
            assert handles == 'fake manager'
            return a/b
        #
        fakespace = FakeSpace()
        lldivide = divide.get_llhelper(fakespace)
        assert lldivide(5.0, 2.0) == 2.5

    def test_freeze(self, api):
        @api.func('void foo(void)')
        def foo(space):
            return None
        #
        api._freeze_()
        with pytest.raises(RuntimeError) as exc:
            @api.func('void bar(void)')
            def bar(space):
                return None
        assert 'Too late to call' in str(exc)

    def test_gil_acquire(self, api):
        from rpython.rtyper.debug import FatalError
        class FakeState:
            def get_handle_manager(self, *args):
                return 'fake manager'

        class FakeSpace:
            @staticmethod
            def fromcache(cls):
                return FakeState()

        fakespace = FakeSpace()
        @api.func('void foo(void)')
        def foo(space, handles):
            from rpython.rlib import rgil
            return rgil.am_I_holding_the_GIL()

        llfoo = foo.get_llhelper(fakespace)

        @api.func('void getgil(void)', gil="acquire")
        def getgil(space, handles):
            return None

        llgetgil = getgil.get_llhelper(fakespace)

        @api.func('void dropgil(void)', gil="release")
        def dropgil(space, handles):
            return None

        lldropgil = dropgil.get_llhelper(fakespace)

        # Try to acquire the GIL when it is already held
        with pytest.raises(FatalError) as exc:
            llgetgil()
        assert 'GIL deadlock detected' in str(exc)
        
        # Make sure the GIL is held automatically even if it was released
        lldropgil()
        assert llfoo()

        # Try to release the GIL twice
        with pytest.raises(FatalError) as exc:
            lldropgil()
        assert 'GIL not held' in str(exc)

