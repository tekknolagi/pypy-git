#include <Python.h>
#include <stdarg.h>

#ifdef CPYEXT_TESTS
#define PyTuplePack _cpyexttestTuplePack
#ifdef __GNUC__
__attribute__((visibility("default")))
#else
__declspec(dllexport)
#endif
#else  /* CPYEXT_TESTS */
#define PyTuplePack PyPyTuplePack
#endif  /* CPYEXT_TESTS */


PyObject *
PyTuple_Pack(Py_ssize_t n, ...)
{
    Py_ssize_t i;
    PyObject *o;
    PyObject *result;
    va_list vargs;

    va_start(vargs, n);
    result = PyTuple_New(n);
    if (result == NULL)
        return NULL;
    for (i = 0; i < n; i++) {
        o = va_arg(vargs, PyObject *);
        Py_INCREF(o);
        if (PyTuple_SetItem(result, i, o) < 0)
            return NULL;
    }
    va_end(vargs);
    return result;
}
