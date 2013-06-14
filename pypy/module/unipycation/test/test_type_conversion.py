import pypy.module.unipycation.conversion as conv

class TestTypeConversion(object):
    spaceconfig = dict(usemodules=('unipycation',))

    def test_int_p_of_int_w(self):
        w_int = self.space.newint(666)
        p_int = conv.int_p_of_int_w(self.space, w_int)

        unwrap1 = self.space.int_w(w_int)
        unwrap2 = p_int.num

        assert unwrap1 == unwrap2

    def test_float_p_of_float_w(self):
        w_float = self.space.newfloat(678.666)
        p_float = conv.float_p_of_float_w(self.space, w_float)

        unwrap1 = self.space.float_w(w_float)
        unwrap2 = p_float.floatval

        assert unwrap1 == unwrap2

    # corner case: test -0.0 converts properly
    def test_float_p_of_float_w_2(self):
        w_float = self.space.newfloat(-0.0)
        p_float = conv.float_p_of_float_w(self.space, w_float)

        unwrap1 = self.space.float_w(w_float)
        unwrap2 = p_float.floatval

        assert unwrap1 == unwrap2

    def test_bigint_p_of_long_w(self):
        w_long = self.space.newlong_from_rbigint(2**65 + 42)
        p_bigint = conv.bigint_p_of_long_w(self.space, w_long)

        unwrap1 = self.space.bigint_w(w_long)
        unwrap2 = p_bigint.value

        assert unwrap1 == unwrap2

    def test_atom_p_of_str_w(self):
        w_str = self.space.wrap("humppa")
        p_atom = conv.atom_p_of_str_w(self.space, w_str)

        unwrap1 = self.space.str_w(w_str)
        unwrap2 = p_atom._signature.name

        assert unwrap1 == unwrap2
