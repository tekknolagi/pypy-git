import py
from rpython.rtyper.lltypesystem import lltype, rffi
from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.translator import cdir
from pypy import pypydir
from rpython.tool.cparser import CTypeSpace

PYPYDIR = py.path.local(pypydir)
SRC_DIR = PYPYDIR.join('module', '_hpy_universal', 'src')
BASE_DIR = PYPYDIR.join('module', '_hpy_universal', '_vendored', 'hpy', 'devel')
INCLUDE_DIR = BASE_DIR.join('include')
DEBUG_DIR = PYPYDIR.join('module', '_hpy_universal', '_vendored', 'hpy', 'debug', 'src')
TRACE_DIR = PYPYDIR.join('module', '_hpy_universal', '_vendored', 'hpy', 'trace', 'src')
CAPI_DIR = PYPYDIR.join('module', '_hpy_universal', 'capi_stub')

HPY_ABI_VERSION = 0
HPY_ABI_VERSION_MINOR = 0
HPY_ABI_TAG = "hpy0"
MODE_INVALID = -1
MODE_UNIVERSAL = 0
MODE_DEBUG = 1
MODE_TRACE = 2


eci = ExternalCompilationInfo(
    compile_extra = ["-DHPY_ABI_HYBRID", "-DHPY_EMBEDDED_MODULES", "-D_HPY_DEBUG_MEM_PROTECT_USEMMAP"],
    includes=["hpy.h", "hpyerr.h", "rffi_hacks.h", "dctx.h", "tctx.h"],
    include_dirs=[
        cdir,                       # for precommondefs.h
        INCLUDE_DIR,                # for universal/hpy.h
        SRC_DIR,                    # for hpyerr.h
        DEBUG_DIR,                  # for debug module
        DEBUG_DIR.join('include'),  # for hpy_debug.h
        TRACE_DIR,                  # for trace module
        TRACE_DIR.join('include'),  # for hpy_trace.h
        CAPI_DIR,                   # for Python.h stub for hybrid tests
    ],
    separate_module_files=[
        SRC_DIR.join('bridge.c'),
        SRC_DIR.join('hpyerr.c'),
        SRC_DIR.join('argparse.c'),
        # <debug mode>
        SRC_DIR.join('dctx.c'),
        DEBUG_DIR.join('debug_ctx.c'),
        DEBUG_DIR.join('debug_ctx_not_cpython.c'),
        DEBUG_DIR.join('debug_handles.c'),
        DEBUG_DIR.join('stacktrace.c'),
        DEBUG_DIR.join('_debugmod.c'),
        DEBUG_DIR.join('autogen_debug_wrappers.c'),
        DEBUG_DIR.join('dhqueue.c'),
        DEBUG_DIR.join('memprotect.c'),
        # </debug mode>
        # <trace mode>
        SRC_DIR.join('tctx.c'),
        TRACE_DIR.join('trace_ctx.c'),
        TRACE_DIR.join('_tracemod.c'),
        TRACE_DIR.join('autogen_trace_wrappers.c'),
        TRACE_DIR.join('autogen_trace_func_table.c'),
        # </trace mode>
        BASE_DIR.join('src', 'runtime', 'ctx_tracker.c'),
    ],
)

cts = CTypeSpace()
cts.headers.append('stdint.h')
cts.parse_source(INCLUDE_DIR.join('hpy', 'autogen_hpyslot.h').read())

# NOTE: the following C source is NOT seen by the C compiler during
# translation: it is used only as a nice way to declare the lltype.* types
# which are needed here
cts.parse_source("""
typedef intptr_t HPy_ssize_t;
typedef intptr_t HPy_hash_t;

struct _HPy_s {
    HPy_ssize_t _i;
};
typedef HPy_ssize_t HPy;

typedef struct _HPyListBuilder_s {
    HPy_ssize_t _lst;
} _struct_HPyListBuilder_s;
typedef HPy_ssize_t HPyListBuilder;

typedef struct _HPyTupleBuilder_s {
    HPy_ssize_t _lst;
} _struct_HPyTupleBuilder_s;
typedef HPy_ssize_t HPyTupleBuilder;

typedef struct _HPyTracker_s {
    HPy_ssize_t _i;
} _struct_HPyTracker_s;
typedef HPy_ssize_t HPyTracker;

typedef struct _HPyField_s {
    HPy_ssize_t _i;
} _struct_HPyField_s;
typedef HPy_ssize_t HPyField;

typedef struct _HPyGlobal_s {
    HPy_ssize_t _i;
} _struct_HPyGlobal_s;
typedef HPy_ssize_t HPyGlobal;

typedef enum {
    HPyType_BuiltinShape_Legacy = -1,
    HPyType_BuiltinShape_Object = 0,
    HPyType_BuiltinShape_Type = 1,
    HPyType_BuiltinShape_Long = 2,
    HPyType_BuiltinShape_Float = 3,
    HPyType_BuiltinShape_Unicode = 4,
    HPyType_BuiltinShape_Tuple = 5,
    HPyType_BuiltinShape_List = 6,
} HPyType_BuiltinShape;

/* sync with lib_pypy/hpy/devel/include/hpy/universal/autogen.h */
typedef struct _HPyContext_s {
    const char *name; // used just to make debugging and testing easier
    void *_private;   // used by implementations to store custom data
    int abi_version;
    struct _HPy_s h_None;
    struct _HPy_s h_True;
    struct _HPy_s h_False;
    struct _HPy_s h_NotImplemented;
    struct _HPy_s h_Ellipsis;
    struct _HPy_s h_BaseException;
    struct _HPy_s h_Exception;
    struct _HPy_s h_StopAsyncIteration;
    struct _HPy_s h_StopIteration;
    struct _HPy_s h_GeneratorExit;
    struct _HPy_s h_ArithmeticError;
    struct _HPy_s h_LookupError;
    struct _HPy_s h_AssertionError;
    struct _HPy_s h_AttributeError;
    struct _HPy_s h_BufferError;
    struct _HPy_s h_EOFError;
    struct _HPy_s h_FloatingPointError;
    struct _HPy_s h_OSError;
    struct _HPy_s h_ImportError;
    struct _HPy_s h_ModuleNotFoundError;
    struct _HPy_s h_IndexError;
    struct _HPy_s h_KeyError;
    struct _HPy_s h_KeyboardInterrupt;
    struct _HPy_s h_MemoryError;
    struct _HPy_s h_NameError;
    struct _HPy_s h_OverflowError;
    struct _HPy_s h_RuntimeError;
    struct _HPy_s h_RecursionError;
    struct _HPy_s h_NotImplementedError;
    struct _HPy_s h_SyntaxError;
    struct _HPy_s h_IndentationError;
    struct _HPy_s h_TabError;
    struct _HPy_s h_ReferenceError;
    struct _HPy_s h_SystemError;
    struct _HPy_s h_SystemExit;
    struct _HPy_s h_TypeError;
    struct _HPy_s h_UnboundLocalError;
    struct _HPy_s h_UnicodeError;
    struct _HPy_s h_UnicodeEncodeError;
    struct _HPy_s h_UnicodeDecodeError;
    struct _HPy_s h_UnicodeTranslateError;
    struct _HPy_s h_ValueError;
    struct _HPy_s h_ZeroDivisionError;
    struct _HPy_s h_BlockingIOError;
    struct _HPy_s h_BrokenPipeError;
    struct _HPy_s h_ChildProcessError;
    struct _HPy_s h_ConnectionError;
    struct _HPy_s h_ConnectionAbortedError;
    struct _HPy_s h_ConnectionRefusedError;
    struct _HPy_s h_ConnectionResetError;
    struct _HPy_s h_FileExistsError;
    struct _HPy_s h_FileNotFoundError;
    struct _HPy_s h_InterruptedError;
    struct _HPy_s h_IsADirectoryError;
    struct _HPy_s h_NotADirectoryError;
    struct _HPy_s h_PermissionError;
    struct _HPy_s h_ProcessLookupError;
    struct _HPy_s h_TimeoutError;
    struct _HPy_s h_Warning;
    struct _HPy_s h_UserWarning;
    struct _HPy_s h_DeprecationWarning;
    struct _HPy_s h_PendingDeprecationWarning;
    struct _HPy_s h_SyntaxWarning;
    struct _HPy_s h_RuntimeWarning;
    struct _HPy_s h_FutureWarning;
    struct _HPy_s h_ImportWarning;
    struct _HPy_s h_UnicodeWarning;
    struct _HPy_s h_BytesWarning;
    struct _HPy_s h_ResourceWarning;
    struct _HPy_s h_BaseObjectType;
    struct _HPy_s h_TypeType;
    struct _HPy_s h_BoolType;
    struct _HPy_s h_LongType;
    struct _HPy_s h_FloatType;
    struct _HPy_s h_UnicodeType;
    struct _HPy_s h_TupleType;
    struct _HPy_s h_ListType;
    void * ctx_Dup;
    void * ctx_Close;
    void * ctx_Long_FromInt32_t;
    void * ctx_Long_FromUInt32_t;
    void * ctx_Long_FromInt64_t;
    void * ctx_Long_FromUInt64_t;
    void * ctx_Long_FromSize_t;
    void * ctx_Long_FromSsize_t;
    void * ctx_Long_AsInt32_t;
    void * ctx_Long_AsUInt32_t;
    void * ctx_Long_AsUInt32_tMask;
    void * ctx_Long_AsInt64_t;
    void * ctx_Long_AsUInt64_t;
    void * ctx_Long_AsUInt64_tMask;
    void * ctx_Long_AsSize_t;
    void * ctx_Long_AsSsize_t;
    void * ctx_Long_AsVoidPtr;
    void * ctx_Long_AsDouble;
    void * ctx_Float_FromDouble;
    void * ctx_Float_AsDouble;
    void * ctx_Bool_FromBool;
    void * ctx_Length;
    void * ctx_Number_Check;
    void * ctx_Add;
    void * ctx_Subtract;
    void * ctx_Multiply;
    void * ctx_MatrixMultiply;
    void * ctx_FloorDivide;
    void * ctx_TrueDivide;
    void * ctx_Remainder;
    void * ctx_Divmod;
    void * ctx_Power;
    void * ctx_Negative;
    void * ctx_Positive;
    void * ctx_Absolute;
    void * ctx_Invert;
    void * ctx_Lshift;
    void * ctx_Rshift;
    void * ctx_And;
    void * ctx_Xor;
    void * ctx_Or;
    void * ctx_Index;
    void * ctx_Long;
    void * ctx_Float;
    void * ctx_InPlaceAdd;
    void * ctx_InPlaceSubtract;
    void * ctx_InPlaceMultiply;
    void * ctx_InPlaceMatrixMultiply;
    void * ctx_InPlaceFloorDivide;
    void * ctx_InPlaceTrueDivide;
    void * ctx_InPlaceRemainder;
    void * ctx_InPlacePower;
    void * ctx_InPlaceLshift;
    void * ctx_InPlaceRshift;
    void * ctx_InPlaceAnd;
    void * ctx_InPlaceXor;
    void * ctx_InPlaceOr;
    void * ctx_Callable_Check;
    void * ctx_CallTupleDict;
    void * ctx_FatalError;
    void * ctx_Err_SetString;
    void * ctx_Err_SetObject;
    void * ctx_Err_SetFromErrnoWithFilename;
    void * ctx_Err_SetFromErrnoWithFilenameObjects;
    void * ctx_Err_Occurred;
    void * ctx_Err_ExceptionMatches;
    void * ctx_Err_NoMemory;
    void * ctx_Err_Clear;
    void * ctx_Err_NewException;
    void * ctx_Err_NewExceptionWithDoc;
    void * ctx_Err_WarnEx;
    void * ctx_Err_WriteUnraisable;
    void * ctx_IsTrue;
    void * ctx_Type_FromSpec;
    void * ctx_Type_GenericNew;
    void * ctx_GetAttr;
    void * ctx_GetAttr_s;
    void * ctx_HasAttr;
    void * ctx_HasAttr_s;
    void * ctx_SetAttr;
    void * ctx_SetAttr_s;
    void * ctx_GetItem;
    void * ctx_GetItem_i;
    void * ctx_GetItem_s;
    void * ctx_Contains;
    void * ctx_SetItem;
    void * ctx_SetItem_i;
    void * ctx_SetItem_s;
    void * ctx_Type;
    void * ctx_TypeCheck;
    void * ctx_Is;
    void * ctx_AsStruct_Object;
    void * ctx_AsStruct_Legacy;
    void * ctx_New;
    void * ctx_Repr;
    void * ctx_Str;
    void * ctx_ASCII;
    void * ctx_Bytes;
    void * ctx_RichCompare;
    void * ctx_RichCompareBool;
    void * ctx_Hash;
    void * ctx_Bytes_Check;
    void * ctx_Bytes_Size;
    void * ctx_Bytes_GET_SIZE;
    void * ctx_Bytes_AsString;
    void * ctx_Bytes_AS_STRING;
    void * ctx_Bytes_FromString;
    void * ctx_Bytes_FromStringAndSize;
    void * ctx_Unicode_FromString;
    void * ctx_Unicode_Check;
    void * ctx_Unicode_AsASCIIString;
    void * ctx_Unicode_AsLatin1String;
    void * ctx_Unicode_AsUTF8String;
    void * ctx_Unicode_AsUTF8AndSize;
    void * ctx_Unicode_FromWideChar;
    void * ctx_Unicode_DecodeFSDefault;
    void * ctx_Unicode_DecodeFSDefaultAndSize;
    void * ctx_Unicode_EncodeFSDefault;
    void * ctx_Unicode_ReadChar;
    void * ctx_Unicode_DecodeASCII;
    void * ctx_Unicode_DecodeLatin1;
    void * ctx_List_Check;
    void * ctx_List_New;
    void * ctx_List_Append;
    void * ctx_Dict_Check;
    void * ctx_Dict_New;
    void * ctx_Tuple_Check;
    void * ctx_Tuple_FromArray;
    void * ctx_Import_ImportModule;
    void * ctx_FromPyObject;
    void * ctx_AsPyObject;
    void * ctx_CallRealFunctionFromTrampoline;
    void * ctx_ListBuilder_New;
    void * ctx_ListBuilder_Set;
    void * ctx_ListBuilder_Build;
    void * ctx_ListBuilder_Cancel;
    void * ctx_TupleBuilder_New;
    void * ctx_TupleBuilder_Set;
    void * ctx_TupleBuilder_Build;
    void * ctx_TupleBuilder_Cancel;
    void * ctx_Tracker_New;
    void * ctx_Tracker_Add;
    void * ctx_Tracker_ForgetAll;
    void * ctx_Tracker_Close;
    void * ctx_Field_Store;
    void * ctx_Field_Load;
    void * ctx_ReenterPythonExecution;
    void * ctx_LeavePythonExecution;
    void * ctx_Global_Store;
    void * ctx_Global_Load;
    void * ctx_Dump;
    void * ctx_AsStruct_Type;
    void * ctx_AsStruct_Long;
    void * ctx_AsStruct_Float;
    void * ctx_AsStruct_Unicode;
    void * ctx_AsStruct_Tuple;
    void * ctx_AsStruct_List;
    void * ctx_Type_GetBuiltinShape;
    void * ctx_DelItem;
    void * ctx_DelItem_i;
    void * ctx_DelItem_s;
    struct _HPy_s h_ComplexType;
    struct _HPy_s h_BytesType;
    struct _HPy_s h_MemoryViewType;
    struct _HPy_s h_CapsuleType;
    struct _HPy_s h_SliceType;
    struct _HPy_s h_Builtins;
    void * ctx_Capsule_New;
    void * ctx_Capsule_Get;
    void * ctx_Capsule_IsValid;
    void * ctx_Capsule_Set;
    void * ctx_Compile_s;
    void * ctx_EvalCode;
    void * ctx_ContextVar_New;
    void * ctx_ContextVar_Get;
    void * ctx_ContextVar_Set;
    void * ctx_Type_GetName;
    void * ctx_Type_IsSubtype;
    void * ctx_Unicode_FromEncodedObject;
    void * ctx_Unicode_Substring;
    void * ctx_Dict_Keys;
    void * ctx_Dict_Copy;
    void * ctx_Slice_Unpack;
    void * ctx_SetCallFunction;
    void * ctx_Call;
    void * ctx_CallMethod;
} _struct_HPyContext_s;

typedef struct _HPyContext_s HPyContext;

typedef int HPyFunc_Signature;

/* hpydef.h */

typedef void* (*HPyCFunction)(void);

typedef struct {
    HPySlot_Slot slot;     // The slot to fill
    HPyCFunction impl;     // Function pointer to the implementation
    void *cpy_trampoline;  // Used by CPython to call impl
} HPySlot;

typedef struct {
    const char *name;             // The name of the built-in function/method
    HPyCFunction impl;            // Function pointer to the implementation
    void *cpy_trampoline;         // Used by CPython to call impl
    HPyFunc_Signature signature;  // Indicates impl's expected the signature
    const char *doc;              // The __doc__ attribute, or NULL
} HPyMeth;

typedef enum {
    HPyMember_SHORT = 0,
    HPyMember_INT = 1,
    HPyMember_LONG = 2,
    HPyMember_FLOAT = 3,
    HPyMember_DOUBLE = 4,
    HPyMember_STRING = 5,
    HPyMember_OBJECT = 6,
    HPyMember_CHAR = 7,   /* 1-character string */
    HPyMember_BYTE = 8,   /* 8-bit signed int */
    /* unsigned variants: */
    HPyMember_UBYTE = 9,
    HPyMember_USHORT = 10,
    HPyMember_UINT = 11,
    HPyMember_ULONG = 12,

    /* Added by Jack: strings contained in the structure */
    HPyMember_STRING_INPLACE = 13,

    /* Added by Lillo: bools contained in the structure (assumed char) */
    HPyMember_BOOL = 14,
    HPyMember_OBJECT_EX = 16,  /* Like T_OBJECT, but raises AttributeError
                                  when the value is NULL, instead of
                                  converting to None. */
    HPyMember_LONGLONG = 17,
    HPyMember_ULONGLONG = 18,

    HPyMember_HPYSSIZET = 19,  /* HPy_ssize_t */
    HPyMember_NONE = 20,       /* Value is always None */

} HPyMember_FieldType;

typedef struct {
    const char *name;
    HPyMember_FieldType type;
    HPy_ssize_t offset;
    int readonly;
    const char *doc;
} HPyMember;

typedef struct {
    const char *name;
    void *getter_impl;            // Function pointer to the implementation
    void *setter_impl;            // Same; this may be NULL
    void *getter_cpy_trampoline;  // Used by CPython to call getter_impl
    void *setter_cpy_trampoline;  // Same; this may be NULL
    const char *doc;
    void *closure;
} HPyGetSet;

typedef enum {
    HPyDef_Kind_Slot = 1,
    HPyDef_Kind_Meth = 2,
    HPyDef_Kind_Member = 3,
    HPyDef_Kind_GetSet = 4,
} HPyDef_Kind;

typedef struct {
    HPyDef_Kind kind;
    //union {
    //    HPySlot slot;
        HPyMeth meth;
        // HPyMember member;
        // HPyGetSet getset;
    //};
} HPyDef;

// work around rffi's lack of support for unions
typedef struct {
    HPyDef_Kind kind;
    HPySlot slot;
} _pypy_HPyDef_as_slot;

typedef struct {
    HPyDef_Kind kind;
    HPyMember member;
} _pypy_HPyDef_as_member;

typedef struct {
    HPyDef_Kind kind;
    HPyGetSet getset;
} _pypy_HPyDef_as_getset;
 
typedef void (*HPyFunc_Capsule_Destructor)(const char *name, void *pointer, void *context);
typedef HPy (*HPyFunc_keywords)(HPyContext *ctx, HPy self, HPy *args, HPy_ssize_t nargs, HPy kw);

typedef struct {
    void *cpy_trampoline;
    HPyFunc_Capsule_Destructor impl;
} HPyCapsule_Destructor;

typedef struct {
    void *pointer;
    const char *name;
    void *context;
    HPyCapsule_Destructor destructor;
} HPyCapsule;

typedef struct {
    void *cpy_trampoline;
    HPyFunc_keywords impl;
} HPyCallFunction;

/* hpymodule.h */

typedef void cpy_PyMethodDef;

typedef struct {
    const char* doc;
    HPy_ssize_t size;
    cpy_PyMethodDef *legacy_methods;
    HPyDef **defines;   /* points to an array of 'HPyDef *' */
    HPyGlobal **globals;
} HPyModuleDef;

/* hpytype.h */

typedef struct {
    const char* name;
    int basicsize;
    int itemsize;
    unsigned long flags;
    HPyType_BuiltinShape builtin_shape;
    void *legacy_slots; // PyType_Slot *
    HPyDef **defines;   /* points to an array of 'HPyDef *' */
    const char* doc;    /* UTF-8 doc string or NULL */
} HPyType_Spec;

typedef enum {
    HPyType_SpecParam_Base = 1,
    HPyType_SpecParam_BasesTuple = 2,
    HPyType_SpecParam_Metaclass = 3,
    HPyType_SpecParam_Module = 4,
} HPyType_SpecParam_Kind;

typedef struct {
    HPyType_SpecParam_Kind kind;
    struct _HPy_s object;
} HPyType_SpecParam;

/* All types are dynamically allocated */
#define _Py_TPFLAGS_HEAPTYPE (1UL << 9)
#define _Py_TPFLAGS_HAVE_VERSION_TAG (1UL << 18)
#define HPy_TPFLAGS_DEFAULT (_Py_TPFLAGS_HEAPTYPE | _Py_TPFLAGS_HAVE_VERSION_TAG)

#define HPy_TPFLAGS_INTERNAL_PURE (1UL << 8)

/* Set if the type allows subclassing */
#define HPy_TPFLAGS_BASETYPE (1UL << 10)

/* macros.h */

/* Rich comparison opcodes */
typedef enum {
    HPy_LT = 0,
    HPy_LE = 1,
    HPy_EQ = 2,
    HPy_NE = 3,
    HPy_GT = 4,
    HPy_GE = 5,
} HPy_RichCmpOp;

/* hpyfunc.h */

typedef struct {
    void *buf;
    struct _HPy_s obj;        /* owned reference */
    HPy_ssize_t len;
    HPy_ssize_t itemsize;
    int readonly;
    int ndim;
    char *format;
    HPy_ssize_t *shape;
    HPy_ssize_t *strides;
    HPy_ssize_t *suboffsets;
    void *internal;
} HPy_buffer;

typedef int (*HPyFunc_visitproc)(HPyField *, void *);

typedef int (*VersionGetterFuncPtr)(void);
typedef HPyModuleDef* (*InitFuncPtr)(void);
typedef void (*InitContextFuncPtr)(HPyContext*);

/* autogen_hpyfunc_declare.h */

typedef HPy (*HPyFunc_noargs)(HPyContext *ctx, HPy self);
typedef HPy (*HPyFunc_o)(HPyContext *ctx, HPy self, HPy arg);
typedef HPy (*HPyFunc_varargs)(HPyContext *ctx, HPy self, HPy *args, HPy_ssize_t nargs);
typedef HPy (*HPyFunc_unaryfunc)(HPyContext *ctx, HPy);
typedef HPy (*HPyFunc_binaryfunc)(HPyContext *ctx, HPy, HPy);
typedef HPy (*HPyFunc_ternaryfunc)(HPyContext *ctx, HPy, HPy, HPy);
typedef int (*HPyFunc_inquiry)(HPyContext *ctx, HPy);
typedef HPy_ssize_t (*HPyFunc_lenfunc)(HPyContext *ctx, HPy);
typedef HPy (*HPyFunc_ssizeargfunc)(HPyContext *ctx, HPy, HPy_ssize_t);
typedef HPy (*HPyFunc_ssizessizeargfunc)(HPyContext *ctx, HPy, HPy_ssize_t, HPy_ssize_t);
typedef int (*HPyFunc_ssizeobjargproc)(HPyContext *ctx, HPy, HPy_ssize_t, HPy);
typedef int (*HPyFunc_ssizessizeobjargproc)(HPyContext *ctx, HPy, HPy_ssize_t, HPy_ssize_t, HPy);
typedef int (*HPyFunc_objobjargproc)(HPyContext *ctx, HPy, HPy, HPy);
typedef void (*HPyFunc_freefunc)(HPyContext *ctx, void *);
typedef HPy (*HPyFunc_getattrfunc)(HPyContext *ctx, HPy, char *);
typedef HPy (*HPyFunc_getattrofunc)(HPyContext *ctx, HPy, HPy);
typedef int (*HPyFunc_setattrfunc)(HPyContext *ctx, HPy, char *, HPy);
typedef int (*HPyFunc_setattrofunc)(HPyContext *ctx, HPy, HPy, HPy);
typedef HPy (*HPyFunc_reprfunc)(HPyContext *ctx, HPy);
typedef HPy_hash_t (*HPyFunc_hashfunc)(HPyContext *ctx, HPy);
typedef HPy (*HPyFunc_richcmpfunc)(HPyContext *ctx, HPy, HPy, int);
typedef HPy (*HPyFunc_getiterfunc)(HPyContext *ctx, HPy);
typedef HPy (*HPyFunc_iternextfunc)(HPyContext *ctx, HPy);
typedef HPy (*HPyFunc_descrgetfunc)(HPyContext *ctx, HPy, HPy, HPy);
typedef int (*HPyFunc_descrsetfunc)(HPyContext *ctx, HPy, HPy, HPy);
typedef int (*HPyFunc_initproc)(HPyContext *ctx, HPy self, HPy *args, HPy_ssize_t nargs, HPy kw);
typedef HPy (*HPyFunc_getter)(HPyContext *ctx, HPy, void *);
typedef int (*HPyFunc_setter)(HPyContext *ctx, HPy, HPy, void *);
typedef int (*HPyFunc_objobjproc)(HPyContext *ctx, HPy, HPy);
typedef int (*HPyFunc_getbufferproc)(HPyContext *ctx, HPy, HPy_buffer *, int);
typedef void (*HPyFunc_releasebufferproc)(HPyContext *ctx, HPy, HPy_buffer *);
typedef int (*HPyFunc_traverseproc)(void *object, HPyFunc_visitproc visit, void *arg);
typedef void (*HPyFunc_destroyfunc)(void *);

/* hpy.h */

struct _HPyThreadState { intptr_t _i; };
typedef intptr_t HPyThreadState;

typedef enum {
    /** Parse isolated expressions (e.g. ``a + b``). */
    HPy_SourceKind_Expr = 0,

    /**
     * Parse sequences of statements as read from a file or other source. This
     * is the symbol to use when compiling arbitrarily long Python source code.
     */
    HPy_SourceKind_File = 1,

    /**
     * Parse a single statement. This is the mode used for the interactive
     * interpreter loop.
     */
    HPy_SourceKind_Single = 2,
} HPy_SourceKind;

typedef enum {
    HPyCapsule_key_Pointer = 0,
    HPyCapsule_key_Name = 1,
    HPyCapsule_key_Context = 2,
    HPyCapsule_key_Destructor = 3,
} _HPyCapsule_key;

""")

# HACK! We manually assign _hints['eci'] to ensure that the eci is included in
# the translation, else common_header.h does not include hpy.h. A more proper
# solution probably involves telling CTypeSpace which eci the types come from?
HPyContext = cts.gettype('HPyContext*')
HPyContext.TO._hints['eci'] = eci

# Hack required to allocate contexts statically:
HPyContext.TO._hints['get_padding_drop'] = lambda d: [name for name in d if name.startswith('c__pad')]

HPy_ssize_t = cts.gettype('HPy_ssize_t')

# for practical reason, we use a primitive type to represent HPy almost
# everywhere in RPython: for example, rffi cannot handle functions returning
# structs. HOWEVER, the "real" HPy C type is a struct, which is available as
# "struct _HPy_s"
HPy = cts.gettype('HPy')
HPy_NULL = rffi.cast(HPy, 0)

cpy_PyMethodDef = cts.gettype('cpy_PyMethodDef')
HPyModuleDef = cts.gettype('HPyModuleDef')
HPyModuleDefP = cts.gettype('HPyModuleDef *')
VersionGetterFuncPtr = cts.gettype('VersionGetterFuncPtr')
InitFuncPtr = cts.gettype('InitFuncPtr')
InitContextFuncPtr = cts.gettype('InitContextFuncPtr')
# CTypeSpace converts "PyMethodDef*" into lltype.Ptr(PyMethodDef), but we
# want a CArrayPtr instead
HPyModuleDef._flds['c_legacy_methods'] = rffi.CArrayPtr(cpy_PyMethodDef)

# enum HPyFunc_Signature {
HPyFunc_VARARGS  = 1
HPyFunc_KEYWORDS = 2
HPyFunc_NOARGS   = 3
HPyFunc_O        = 4
# ...
# }

HPyType_SpecParam_Kind = cts.gettype('HPyType_SpecParam_Kind')
HPyThreadState = cts.gettype("HPyThreadState")

HPy_TPFLAGS_INTERNAL_PURE = (1 << 8)
HPy_TPFLAGS_HAVE_GC =  1 << 14

# HPy API functions which are implemented directly in C
pypy_HPy_FatalError = rffi.llexternal(
        'pypy_HPy_FatalError',
        [HPyContext, rffi.CCHARP],
        lltype.Void,
        compilation_info=eci, _nowrapper=True)

# debug mode
hpy_debug_get_ctx = rffi.llexternal(
    'pypy_hpy_debug_get_ctx', [HPyContext], HPyContext,
    compilation_info=eci, _nowrapper=True)

hpy_debug_ctx_init = rffi.llexternal(
    'pypy_hpy_debug_ctx_init', [HPyContext, HPyContext], rffi.INT_real,
    compilation_info=eci, _nowrapper=True)

hpy_debug_set_ctx = rffi.llexternal(
    'pypy_hpy_debug_set_ctx', [HPyContext], lltype.Void,
    compilation_info=eci, _nowrapper=True)

hpy_debug_open_handle = rffi.llexternal(
    'pypy_hpy_debug_open_handle', [HPyContext, HPy], HPy,
    compilation_info=eci, _nowrapper=True)

hpy_debug_unwrap_handle = rffi.llexternal(
    'pypy_hpy_debug_unwrap_handle', [HPyContext, HPy], HPy,
    compilation_info=eci, _nowrapper=True)

hpy_debug_close_handle = rffi.llexternal(
    'pypy_hpy_debug_close_handle', [HPyContext, HPy], lltype.Void,
    compilation_info=eci, _nowrapper=True)

HPyInit__debug = rffi.llexternal(
    'pypy_HPyInit__debug', [], HPyModuleDefP,
    compilation_info=eci, _nowrapper=True)

#trace mode
hpy_trace_get_ctx = rffi.llexternal(
    'pypy_hpy_trace_get_ctx', [HPyContext], HPyContext,
    compilation_info=eci, _nowrapper=True)

hpy_trace_ctx_init = rffi.llexternal(
    'pypy_hpy_trace_ctx_init', [HPyContext, HPyContext], rffi.INT_real,
    compilation_info=eci, _nowrapper=True)

hpy_trace_ctx_free = rffi.llexternal(
    'pypy_hpy_trace_ctx_free', [HPyContext], rffi.INT_real,
    compilation_info=eci, _nowrapper=True)

hpy_trace_get_func_name = rffi.llexternal(
    'pypy_hpy_trace_get_func_name', [rffi.INT_real], rffi.CCHARP,
    compilation_info=eci, _nowrapper=True)

hpy_trace_get_nfunc = rffi.llexternal(
    'pypy_hpy_trace_get_nfunc', [], rffi.INT_real,
    compilation_info=eci, _nowrapper=True)

HPyInit__trace = rffi.llexternal(
    'pypy_HPyInit__trace', [], HPyModuleDefP,
    compilation_info=eci, _nowrapper=True)
