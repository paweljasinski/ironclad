
from tools.dispatchersnippets import *

# args for generate_dispatcher_field
dispatcher_field_types = (
    (('int', 'int', 'Int'), {}),
    (('ubyte', 'byte', 'Byte'), {}),
    (('char', 'string', 'Byte'), {'gettweak': 'Builtin.chr', 'settweak': '(byte)Builtin.ord'}),
)

# args for generate_dispatcher_method
dispatcher_PyCFunc_convenience_methods = (
    (('ic_function_noargs', 'obj_objobj'), {'argtweak': ('null', 'null')}),
    (('ic_method_noargs', 'obj_objobj'), {'argtweak': (0, 'null')}),
    (('ic_function_objarg', 'obj_objobj'), {'argtweak': ('null', 0)}),
    (('ic_method_objarg', 'obj_objobj'), {}),
    (('ic_function_varargs', 'obj_objobj'), {'argtweak': ('null', 0)}),
    (('ic_method_varargs', 'obj_objobj'), {}),
    (('ic_function_kwargs', 'obj_objobjobj'), {'argtweak': ('null', 0, 1), 'nullablekwargs': 1}),
    (('ic_method_kwargs', 'obj_objobjobj'), {'nullablekwargs': 2}),
    
    (('ic_method_getter', 'obj_objptr'), {}),
    (('ic_method_setter', 'int_objobjptr'), {'rettweak': THROW_RET_NEGATIVE}),
)

# args for generate_dispatcher_method
dispatcher_header_functypes = (
    # object.h
    (('unaryfunc', 'obj_obj'), {}),
    (('binaryfunc', 'obj_objobj'), {}),
    (('ternaryfunc', 'obj_objobjobj'), {}),
    (('inquiry', 'int_obj'), {}),
    (('lenfunc', 'size_obj'), {}),
    (('coercion', 'int_ptrptr'), {}),
    (('intargfunc', 'obj_objint'), {}),
    (('intintargfunc', 'obj_objintint'), {}),
    (('ssizeargfunc', 'obj_objsize'), {}),
    (('ssizessizeargfunc', 'obj_objsizesize'), {}),
    (('intobjargproc', 'int_objintobj'), {}),
    (('intintobjargproc', 'int_objintintobj'), {}),
    (('ssizeobjargproc', 'int_objsizeobj'), {}),
    (('ssizessizeobjargproc', 'int_objsizesizeobj'), {}),
    (('objobjargproc', 'int_objobjobj'), {}),

    (('getreadbufferproc', 'int_objintptr'), {}),
    (('getwritebufferproc', 'int_objintptr'), {}),
    (('getsegcountproc', 'int_objptr'), {}),
    (('getcharbufferproc', 'int_objintptr'), {}),
    (('readbufferproc', 'size_objsizeptr'), {}),
    (('writebufferproc', 'size_objsizeptr'), {}),
    (('segcountproc', 'size_objptr'), {}),
    (('charbufferproc', 'size_objsizeptr'), {}),
    
    (('objobjproc', 'int_objobj'), {}),
    (('visitproc', 'int_objptr'), {}),
    (('traverseproc', 'int_objptrptr'), {}),
    
    (('freefunc', 'void_ptr'), {}),
    (('destructor', 'void_obj'), {'rettweak': HANDLE_RET_DESTRUCTOR}),
    (('printfunc', 'int_objptrint'), {}),
    (('getattrfunc', 'obj_objstr'), {}),
    (('getattrofunc', 'obj_objobj'), {}),
    (('setattrfunc', 'int_objstrobj'), {}),
    (('setattrofunc', 'int_objobjobj'), {}),
    (('cmpfunc', 'int_objobj'), {}),
    (('reprfunc', 'obj_obj'), {}),
    (('hashfunc', 'long_obj'), {}),
    (('richcmpfunc', 'obj_objobjint'), {}),
    (('getiterfunc', 'obj_obj'), {}),
    (('iternextfunc', 'obj_obj'), {'rettweak': ITERNEXT_HANDLE_RETPTR}),
    (('descrgetfunc', 'obj_objobjobj'), {}),
    (('descrsetfunc', 'int_objobjobj'), {}),
    (('initproc', 'int_objobjobj'), {'rettweak': THROW_RET_NEGATIVE, 'nullablekwargs': 2}),
    (('newfunc', 'obj_objobjobj'), {'nullablekwargs': 2}),
    (('allocfunc', 'obj_objsize'), {}),
    
    # desrcobject.h
    (('getter', 'obj_objptr'), {}),
    (('setter', 'int_objobjptr'), {}),
)

dispatcher_methods = dispatcher_PyCFunc_convenience_methods + dispatcher_header_functypes

# args for generate_magic_method
protocol_field_types = (
    # note that missing fields, unless noted, just aren't handled yet
    
    # PyTypeObject
    # new and del should always be set up anyway
    # richcmp is tricky and needs special handling
    (('tp_init', 'initproc', '__init__'), {'template': SQUISHKWARGS_TEMPLATE_TEMPLATE}),
    (('tp_iter', 'getiterfunc', '__iter__'), {}),
    (('tp_iternext', 'iternextfunc', 'next'), {}),
    (('tp_str', 'reprfunc', '__str__'), {}),
    (('tp_repr', 'reprfunc', '__repr__'), {}),
    (('tp_call', 'ternaryfunc', '__call__'), {'template': SQUISHKWARGS_TEMPLATE_TEMPLATE}),
    (('tp_hash', 'hashfunc', '__hash__'), {}),
    (('tp_compare', 'cmpfunc', '__cmp__'), {}),
    (('tp_getattr', 'getattrfunc', '__getattr__'), {}), # tweaks needed eventually? (getattro)
    
    # PyNumberMethods
    # pow, ipow are tricky and need special handling
    (('nb_add', 'binaryfunc', '__add__'), {'swapped': '__radd__'}),
    (('nb_subtract', 'binaryfunc', '__sub__'), {'swapped': '__rsub__'}),
    (('nb_multiply', 'binaryfunc', '__mul__'), {'swapped': '__rmul__'}),
    (('nb_divide', 'binaryfunc', '__div__'), {'swapped': '__rdiv__'}),
    (('nb_remainder', 'binaryfunc', '__mod__'), {'swapped': '__rmod__'}),
    (('nb_divmod', 'binaryfunc', '__divmod__'), {'swapped': '__rdivmod__'}),
    (('nb_power', 'ternaryfunc', '__pow__'), {'swapped': '__rpow__', 'template': POW_TEMPLATE_TEMPLATE, 'swappedtemplate': POW_SWAPPED_TEMPLATE_TEMPLATE}),
    (('nb_negative', 'unaryfunc', '__neg__'), {}),
    (('nb_positive', 'unaryfunc', '__pos__'), {}),
    (('nb_absolute', 'unaryfunc', '__abs__'), {}),
    (('nb_nonzero', 'inquiry', '__nonzero__'), {}),
    (('nb_invert', 'unaryfunc', '__invert__'), {}),
    (('nb_lshift', 'binaryfunc', '__lshift__'), {'swapped': '__rlshift__'}),
    (('nb_rshift', 'binaryfunc', '__rshift__'), {'swapped': '__rrshift__'}),
    (('nb_and', 'binaryfunc', '__and__'), {'swapped': '__rand__'}),
    (('nb_xor', 'binaryfunc', '__xor__'), {'swapped': '__rxor__'}),
    (('nb_or', 'binaryfunc', '__or__'), {'swapped': '__ror__'}),
    (('nb_int', 'unaryfunc', '__int__'), {}),
    (('nb_long', 'unaryfunc', '__long__'), {}),
    (('nb_float', 'unaryfunc', '__float__'), {}),
    (('nb_oct', 'unaryfunc', '__oct__'), {}),
    (('nb_hex', 'unaryfunc', '__hex__'), {}),
    (('nb_inplace_add', 'binaryfunc', '__iadd__'), {}),
    (('nb_inplace_subtract', 'binaryfunc', '__isub__'), {}),
    (('nb_inplace_multiply', 'binaryfunc', '__imul__'), {}),
    (('nb_inplace_divide', 'binaryfunc', '__idiv__'), {}),
    (('nb_inplace_remainder', 'binaryfunc', '__imod__'), {}),
    (('nb_inplace_power', 'ternaryfunc', '__ipow__'), {'template': POW_TEMPLATE_TEMPLATE}),
    (('nb_inplace_lshift', 'binaryfunc', '__ilshift__'), {}),
    (('nb_inplace_rshift', 'binaryfunc', '__irshift__'), {}),
    (('nb_inplace_and', 'binaryfunc', '__iand__'), {}),
    (('nb_inplace_xor', 'binaryfunc', '__ixor__'), {}),
    (('nb_inplace_or', 'binaryfunc', '__ior__'), {}),
    (('nb_true_divide', 'binaryfunc', '__truediv__'), {'swapped': '__rtruediv__'}),
    (('nb_floor_divide', 'binaryfunc', '__floordiv__'), {'swapped': '__rfloordiv__'}),
    (('nb_inplace_true_divide', 'binaryfunc', '__itruediv__'), {}),
    (('nb_inplace_floor_divide', 'binaryfunc', '__ifloordiv__'), {}),
    (('nb_index', 'unaryfunc', '__index__'), {}),

    # PySequenceMethods
    (('sq_length', 'lenfunc', '__len__'), {}),
    (('sq_concat', 'binaryfunc', '__add__'), {}),
    (('sq_item', 'ssizeargfunc', '__getitem__'), {}),
    (('sq_slice', 'ssizessizeargfunc', '__getslice__'), {}),
    (('sq_ass_item', 'ssizeobjargproc', '__setitem__'), {}),
    (('sq_ass_slice', 'ssizessizeobjargproc', '__setslice__'), {}),
    
    # PyMappingMethods
    (('mp_length', 'lenfunc', '__len__'), {}),
    (('mp_subscript', 'binaryfunc', '__getitem__'), {}),
    (('mp_ass_subscript', 'objobjargproc', '__setitem__'), {}),
)
