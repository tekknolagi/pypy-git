
/* Module support implementation */

#include "Python.h"

#define FLAG_SIZE_T 1
typedef double va_double;

static PyObject *va_build_value(const char *, va_list, int);
static PyObject **va_build_stack(PyObject **small_stack, Py_ssize_t small_stack_len, const char *, va_list, int, Py_ssize_t*);

/* Package context -- the full module name for package imports */
const char *_Py_PackageContext = NULL;


int
_Py_convert_optional_to_ssize_t(PyObject *obj, void *result)
{
    Py_ssize_t limit;
    if (obj == Py_None) {
        return 1;
    }
    else if (PyIndex_Check(obj)) {
        limit = PyNumber_AsSsize_t(obj, PyExc_OverflowError);
        if (limit == -1 && PyErr_Occurred()) {
            return 0;
        }
    }
    else {
        PyErr_Format(PyExc_TypeError,
                     "argument should be integer or None, not '%.200s'",
                     Py_TYPE(obj)->tp_name);
        return 0;
    }
    *((Py_ssize_t *)result) = limit;
    return 1;
}


/* Helper for mkvalue() to scan the length of a format */

static Py_ssize_t
countformat(const char *format, char endchar)
{
    Py_ssize_t count = 0;
    int level = 0;
    while (level > 0 || *format != endchar) {
        switch (*format) {
        case '\0':
            /* Premature end */
            PyErr_SetString(PyExc_SystemError,
                            "unmatched paren in format");
            return -1;
        case '(':
        case '[':
        case '{':
            if (level == 0) {
                count++;
            }
            level++;
            break;
        case ')':
        case ']':
        case '}':
            level--;
            break;
        case '#':
        case '&':
        case ',':
        case ':':
        case ' ':
        case '\t':
            break;
        default:
            if (level == 0) {
                count++;
            }
        }
        format++;
    }
    return count;
}


/* Generic function to create a value -- the inverse of getargs() */
/* After an original idea and first implementation by Steven Miale */

static PyObject *do_mktuple(const char**, va_list *, char, Py_ssize_t, int);
static int do_mkstack(PyObject **, const char**, va_list *, char, Py_ssize_t, int);
static PyObject *do_mklist(const char**, va_list *, char, Py_ssize_t, int);
static PyObject *do_mkdict(const char**, va_list *, char, Py_ssize_t, int);
static PyObject *do_mkvalue(const char**, va_list *, int);


static void
do_ignore(const char **p_format, va_list *p_va, char endchar, Py_ssize_t n, int flags)
{
    PyObject *v;
    Py_ssize_t i;
    assert(PyErr_Occurred());
    v = PyTuple_New(n);
    for (i = 0; i < n; i++) {
        PyObject *exception, *value, *tb, *w;

        PyErr_Fetch(&exception, &value, &tb);
        w = do_mkvalue(p_format, p_va, flags);
        PyErr_Restore(exception, value, tb);
        if (w != NULL) {
            if (v != NULL) {
                PyTuple_SET_ITEM(v, i, w);
            }
            else {
                Py_DECREF(w);
            }
        }
    }
    Py_XDECREF(v);
    if (**p_format != endchar) {
        PyErr_SetString(PyExc_SystemError,
                        "Unmatched paren in format");
        return;
    }
    if (endchar) {
        ++*p_format;
    }
}

static PyObject *
do_mkdict(const char **p_format, va_list *p_va, char endchar, Py_ssize_t n, int flags)
{
    PyObject *d;
    Py_ssize_t i;
    if (n < 0)
        return NULL;
    if (n % 2) {
        PyErr_SetString(PyExc_SystemError,
                        "Bad dict format");
        do_ignore(p_format, p_va, endchar, n, flags);
        return NULL;
    }
    /* Note that we can't bail immediately on error as this will leak
       refcounts on any 'N' arguments. */
    if ((d = PyDict_New()) == NULL) {
        do_ignore(p_format, p_va, endchar, n, flags);
        return NULL;
    }
    for (i = 0; i < n; i+= 2) {
        PyObject *k, *v;

        k = do_mkvalue(p_format, p_va, flags);
        if (k == NULL) {
            do_ignore(p_format, p_va, endchar, n - i - 1, flags);
            Py_DECREF(d);
            return NULL;
        }
        v = do_mkvalue(p_format, p_va, flags);
        if (v == NULL || PyDict_SetItem(d, k, v) < 0) {
            do_ignore(p_format, p_va, endchar, n - i - 2, flags);
            Py_DECREF(k);
            Py_XDECREF(v);
            Py_DECREF(d);
            return NULL;
        }
        Py_DECREF(k);
        Py_DECREF(v);
    }
    if (**p_format != endchar) {
        Py_DECREF(d);
        PyErr_SetString(PyExc_SystemError,
                        "Unmatched paren in format");
        return NULL;
    }
    if (endchar)
        ++*p_format;
    return d;
}

static PyObject *
do_mklist(const char **p_format, va_list *p_va, char endchar, Py_ssize_t n, int flags)
{
    PyObject *v;
    Py_ssize_t i;
    if (n < 0)
        return NULL;
    /* Note that we can't bail immediately on error as this will leak
       refcounts on any 'N' arguments. */
    v = PyList_New(n);
    if (v == NULL) {
        do_ignore(p_format, p_va, endchar, n, flags);
        return NULL;
    }
    for (i = 0; i < n; i++) {
        PyObject *w = do_mkvalue(p_format, p_va, flags);
        if (w == NULL) {
            do_ignore(p_format, p_va, endchar, n - i - 1, flags);
            Py_DECREF(v);
            return NULL;
        }
        PyList_SET_ITEM(v, i, w);
    }
    if (**p_format != endchar) {
        Py_DECREF(v);
        PyErr_SetString(PyExc_SystemError,
                        "Unmatched paren in format");
        return NULL;
    }
    if (endchar)
        ++*p_format;
    return v;
}

static int
do_mkstack(PyObject **stack, const char **p_format, va_list *p_va,
           char endchar, Py_ssize_t n, int flags)
{
    Py_ssize_t i;

    if (n < 0) {
        return -1;
    }
    /* Note that we can't bail immediately on error as this will leak
       refcounts on any 'N' arguments. */
    for (i = 0; i < n; i++) {
        PyObject *w = do_mkvalue(p_format, p_va, flags);
        if (w == NULL) {
            do_ignore(p_format, p_va, endchar, n - i - 1, flags);
            goto error;
        }
        stack[i] = w;
    }
    if (**p_format != endchar) {
        PyErr_SetString(PyExc_SystemError,
                        "Unmatched paren in format");
        goto error;
    }
    if (endchar) {
        ++*p_format;
    }
    return 0;

error:
    n = i;
    for (i=0; i < n; i++) {
        Py_DECREF(stack[i]);
    }
    return -1;
}

static PyObject *
do_mktuple(const char **p_format, va_list *p_va, char endchar, Py_ssize_t n, int flags)
{
    PyObject *v;
    Py_ssize_t i;
    if (n < 0)
        return NULL;
    /* Note that we can't bail immediately on error as this will leak
       refcounts on any 'N' arguments. */
    if ((v = PyTuple_New(n)) == NULL) {
        do_ignore(p_format, p_va, endchar, n, flags);
        return NULL;
    }
    for (i = 0; i < n; i++) {
        PyObject *w = do_mkvalue(p_format, p_va, flags);
        if (w == NULL) {
            do_ignore(p_format, p_va, endchar, n - i - 1, flags);
            Py_DECREF(v);
            return NULL;
        }
        PyTuple_SET_ITEM(v, i, w);
    }
    if (**p_format != endchar) {
        Py_DECREF(v);
        PyErr_SetString(PyExc_SystemError,
                        "Unmatched paren in format");
        return NULL;
    }
    if (endchar)
        ++*p_format;
    return v;
}

static PyObject *
do_mkvalue(const char **p_format, va_list *p_va, int flags)
{
#define ERROR_NEED_PY_SSIZE_T_CLEAN \
    { \
        PyErr_SetString(PyExc_SystemError, \
                        "PY_SSIZE_T_CLEAN macro must be defined for '#' formats"); \
        return NULL; \
    }

    for (;;) {
        switch (*(*p_format)++) {
        case '(':
            return do_mktuple(p_format, p_va, ')',
                              countformat(*p_format, ')'), flags);

        case '[':
            return do_mklist(p_format, p_va, ']',
                             countformat(*p_format, ']'), flags);

        case '{':
            return do_mkdict(p_format, p_va, '}',
                             countformat(*p_format, '}'), flags);

        case 'b':
        case 'B':
        case 'h':
        case 'i':
            return PyLong_FromLong((long)va_arg(*p_va, int));

        case 'H':
            return PyLong_FromLong((long)va_arg(*p_va, unsigned int));

        case 'I':
        {
            unsigned int n;
            n = va_arg(*p_va, unsigned int);
            return PyLong_FromUnsignedLong(n);
        }

        case 'n':
#if SIZEOF_SIZE_T!=SIZEOF_LONG
            return PyLong_FromSsize_t(va_arg(*p_va, Py_ssize_t));
#endif
            /* Fall through from 'n' to 'l' if Py_ssize_t is long */
        case 'l':
            return PyLong_FromLong(va_arg(*p_va, long));

        case 'k':
        {
            unsigned long n;
            n = va_arg(*p_va, unsigned long);
            return PyLong_FromUnsignedLong(n);
        }

        case 'L':
            return PyLong_FromLongLong((long long)va_arg(*p_va, long long));

        case 'K':
            return PyLong_FromUnsignedLongLong((long long)va_arg(*p_va, unsigned long long));

        case 'u':
        {
            PyObject *v;
            Py_UNICODE *u = va_arg(*p_va, Py_UNICODE *);
            Py_ssize_t n;
            if (**p_format == '#') {
                ++*p_format;
                if (flags & FLAG_SIZE_T) {
                    n = va_arg(*p_va, Py_ssize_t);
                }
                else {
                    n = va_arg(*p_va, int);
                    ERROR_NEED_PY_SSIZE_T_CLEAN;
                }
            }
            else
                n = -1;
            if (u == NULL) {
                v = Py_None;
                Py_INCREF(v);
            }
            else {
                if (n < 0)
                    n = wcslen(u);
                v = PyUnicode_FromWideChar(u, n);
            }
            return v;
        }
        case 'f':
        case 'd':
            return PyFloat_FromDouble(
                (double)va_arg(*p_va, va_double));

        case 'D':
            return PyComplex_FromCComplex(
                *((Py_complex *)va_arg(*p_va, Py_complex *)));

        case 'c':
        {
            char p[1];
            p[0] = (char)va_arg(*p_va, int);
            return PyBytes_FromStringAndSize(p, 1);
        }
        case 'C':
        {
            int i = va_arg(*p_va, int);
            return PyUnicode_FromOrdinal(i);
        }

        case 's':
        case 'z':
        case 'U':   /* XXX deprecated alias */
        {
            PyObject *v;
            const char *str = va_arg(*p_va, const char *);
            Py_ssize_t n;
            if (**p_format == '#') {
                ++*p_format;
                if (flags & FLAG_SIZE_T) {
                    n = va_arg(*p_va, Py_ssize_t);
                }
                else {
                    n = va_arg(*p_va, int);
                    ERROR_NEED_PY_SSIZE_T_CLEAN;
                }
            }
            else
                n = -1;
            if (str == NULL) {
                v = Py_None;
                Py_INCREF(v);
            }
            else {
                if (n < 0) {
                    size_t m = strlen(str);
                    if (m > PY_SSIZE_T_MAX) {
                        PyErr_SetString(PyExc_OverflowError,
                            "string too long for Python string");
                        return NULL;
                    }
                    n = (Py_ssize_t)m;
                }
                v = PyUnicode_FromStringAndSize(str, n);
            }
            return v;
        }

        case 'y':
        {
            PyObject *v;
            const char *str = va_arg(*p_va, const char *);
            Py_ssize_t n;
            if (**p_format == '#') {
                ++*p_format;
                if (flags & FLAG_SIZE_T) {
                    n = va_arg(*p_va, Py_ssize_t);
                }
                else {
                    n = va_arg(*p_va, int);
                    ERROR_NEED_PY_SSIZE_T_CLEAN;
                }
            }
            else
                n = -1;
            if (str == NULL) {
                v = Py_None;
                Py_INCREF(v);
            }
            else {
                if (n < 0) {
                    size_t m = strlen(str);
                    if (m > PY_SSIZE_T_MAX) {
                        PyErr_SetString(PyExc_OverflowError,
                            "string too long for Python bytes");
                        return NULL;
                    }
                    n = (Py_ssize_t)m;
                }
                v = PyBytes_FromStringAndSize(str, n);
            }
            return v;
        }

        case 'N':
        case 'S':
        case 'O':
        if (**p_format == '&') {
            typedef PyObject *(*converter)(void *);
            converter func = va_arg(*p_va, converter);
            void *arg = va_arg(*p_va, void *);
            ++*p_format;
            return (*func)(arg);
        }
        else {
            PyObject *v;
            v = va_arg(*p_va, PyObject *);
            if (v != NULL) {
                if (*(*p_format - 1) != 'N')
                    Py_INCREF(v);
            }
            else if (!PyErr_Occurred())
                /* If a NULL was passed
                 * because a call that should
                 * have constructed a value
                 * failed, that's OK, and we
                 * pass the error on; but if
                 * no error occurred it's not
                 * clear that the caller knew
                 * what she was doing. */
                PyErr_SetString(PyExc_SystemError,
                    "NULL object passed to Py_BuildValue");
            return v;
        }

        case ':':
        case ',':
        case ' ':
        case '\t':
            break;

        default:
            PyErr_SetString(PyExc_SystemError,
                "bad format char passed to Py_BuildValue");
            return NULL;

        }
    }

#undef ERROR_NEED_PY_SSIZE_T_CLEAN
}


PyObject *
Py_BuildValue(const char *format, ...)
{
    va_list va;
    PyObject* retval;
    va_start(va, format);
    retval = va_build_value(format, va, 0);
    va_end(va);
    return retval;
}

PyObject *
_Py_BuildValue_SizeT(const char *format, ...)
{
    va_list va;
    PyObject* retval;
    va_start(va, format);
    retval = va_build_value(format, va, FLAG_SIZE_T);
    va_end(va);
    return retval;
}

PyObject *
Py_VaBuildValue(const char *format, va_list va)
{
    return va_build_value(format, va, 0);
}

PyObject *
_Py_VaBuildValue_SizeT(const char *format, va_list va)
{
    return va_build_value(format, va, FLAG_SIZE_T);
}

static PyObject *
va_build_value(const char *format, va_list va, int flags)
{
    const char *f = format;
    Py_ssize_t n = countformat(f, '\0');
    va_list lva;
    PyObject *retval;

    if (n < 0)
        return NULL;
    if (n == 0) {
        Py_RETURN_NONE;
    }
    va_copy(lva, va);
    if (n == 1) {
        retval = do_mkvalue(&f, &lva, flags);
    } else {
        retval = do_mktuple(&f, &lva, '\0', n, flags);
    }
    va_end(lva);
    return retval;
}

PyObject **
_Py_VaBuildStack(PyObject **small_stack, Py_ssize_t small_stack_len,
                const char *format, va_list va, Py_ssize_t *p_nargs)
{
    return va_build_stack(small_stack, small_stack_len, format, va, 0, p_nargs);
}

PyObject **
_Py_VaBuildStack_SizeT(PyObject **small_stack, Py_ssize_t small_stack_len,
                       const char *format, va_list va, Py_ssize_t *p_nargs)
{
    return va_build_stack(small_stack, small_stack_len, format, va, FLAG_SIZE_T, p_nargs);
}

static PyObject **
va_build_stack(PyObject **small_stack, Py_ssize_t small_stack_len,
               const char *format, va_list va, int flags, Py_ssize_t *p_nargs)
{
    const char *f;
    Py_ssize_t n;
    va_list lva;
    PyObject **stack;
    int res;

    n = countformat(format, '\0');
    if (n < 0) {
        *p_nargs = 0;
        return NULL;
    }

    if (n == 0) {
        *p_nargs = 0;
        return small_stack;
    }

    if (n <= small_stack_len) {
        stack = small_stack;
    }
    else {
        stack = PyMem_Malloc(n * sizeof(stack[0]));
        if (stack == NULL) {
            PyErr_NoMemory();
            return NULL;
        }
    }

    va_copy(lva, va);
    f = format;
    res = do_mkstack(stack, &f, &lva, '\0', n, flags);
    va_end(lva);

    if (res < 0) {
        if (stack != small_stack) {
            PyMem_Free(stack);
        }
        return NULL;
    }

    *p_nargs = n;
    return stack;
}


int
PyModule_AddObjectRef(PyObject *mod, const char *name, PyObject *value)
{
    if (!PyModule_Check(mod)) {
        PyErr_SetString(PyExc_TypeError,
                        "PyModule_AddObjectRef() first argument "
                        "must be a module");
        return -1;
    }
    if (!value) {
        if (!PyErr_Occurred()) {
            PyErr_SetString(PyExc_SystemError,
                            "PyModule_AddObjectRef() must be called "
                            "with an exception raised if value is NULL");
        }
        return -1;
    }

    PyObject *dict = PyModule_GetDict(mod);
    if (dict == NULL) {
        /* Internal error -- modules must have a dict! */
        PyErr_Format(PyExc_SystemError, "module '%s' has no __dict__",
                     PyModule_GetName(mod));
        return -1;
    }

    if (PyDict_SetItemString(dict, name, value)) {
        return -1;
    }
    return 0;
}


int
PyModule_AddObject(PyObject *mod, const char *name, PyObject *value)
{
    int res = PyModule_AddObjectRef(mod, name, value);
    if (res == 0) {
        Py_DECREF(value);
    }
    return res;
}

int
PyModule_AddIntConstant(PyObject *m, const char *name, long value)
{
    PyObject *obj = PyLong_FromLong(value);
    if (!obj) {
        return -1;
    }
    int res = PyModule_AddObjectRef(m, name, obj);
    Py_DECREF(obj);
    return res;
}

int
PyModule_AddStringConstant(PyObject *m, const char *name, const char *value)
{
    PyObject *obj = PyUnicode_FromString(value);
    if (!obj) {
        return -1;
    }
    int res = PyModule_AddObjectRef(m, name, obj);
    Py_DECREF(obj);
    return res;
}

int
PyModule_AddType(PyObject *module, PyTypeObject *type)
{
    if (PyType_Ready(type) < 0) {
        return -1;
    }

    const char *name = _PyType_Name(type);
    assert(name != NULL);

    Py_INCREF(type);
    if (PyModule_AddObject(module, name, (PyObject *)type) < 0) {
        Py_DECREF(type);
        return -1;
    }

    return PyModule_AddObjectRef(module, name, (PyObject *)type);
}

PyModuleDef*
PyModule_GetDef(PyObject* m)
{
    if (!PyModule_Check(m)) {
        PyErr_BadArgument();
        return NULL;
    }
    return ((PyModuleObject *)m)->md_def;
}

void*
PyModule_GetState(PyObject* m)
{
    if (!PyModule_Check(m)) {
        PyErr_BadArgument();
        return NULL;
    }
    return ((PyModuleObject *)m)->md_state;
}

PyTypeObject PyModuleDef_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "moduledef",                                /* tp_name */
    sizeof(struct PyModuleDef),                 /* tp_size */
    0,                                          /* tp_itemsize */
};

static Py_ssize_t max_module_number;

PyObject*
PyModuleDef_Init(struct PyModuleDef* def)
{
    if (PyType_Ready(&PyModuleDef_Type) < 0)
         return NULL;
    if (def->m_base.m_index == 0) {
        max_module_number++;
        Py_SET_REFCNT(def, 1);
        Py_SET_TYPE(def, &PyModuleDef_Type);
        def->m_base.m_index = max_module_number;
    }
    return (PyObject*)def;
}

PyObject *
PyType_GetModule(PyTypeObject *type)
{
    assert(PyType_Check(type));
    if (!PyType_HasFeature(type, Py_TPFLAGS_HEAPTYPE)) {
        PyErr_Format(
            PyExc_TypeError,
            "PyType_GetModule: Type '%s' is not a heap type",
            type->tp_name);
        return NULL;
    }

    PyHeapTypeObject* et = (PyHeapTypeObject*)type;
    if (!et->ht_module) {
        PyErr_Format(
            PyExc_TypeError,
            "PyType_GetModule: Type '%s' has no associated module",
            type->tp_name);
        return NULL;
    }
    return et->ht_module;

}

void *
PyType_GetModuleState(PyTypeObject *type)
{
    PyObject *m = PyType_GetModule(type);
    if (m == NULL) {
        return NULL;
    }
    return PyModule_GetState(m);
}

PyObject*
PyState_FindModule(struct PyModuleDef* module)
{
    Py_ssize_t index = module->m_base.m_index;
    PyThreadState *tstate = PyThreadState_Get();
    PyInterpreterState *state = tstate->interp;
    PyObject *res;
    if (module->m_slots) {
        return NULL;
    }
    if (index == 0)
        return NULL;
    if (state->modules_by_index == NULL)
        return NULL;
    if (index >= PyList_GET_SIZE(state->modules_by_index))
        return NULL;
    res = PyList_GET_ITEM(state->modules_by_index, index);
    return res==Py_None ? NULL : res;
}
