
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator, GetDoNothingTestAllocator
from tests.utils.memory import CreateTypes, OffsetPtr

from System import IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import BadRefCountException, CPyMarshal, CPython_destructor_Delegate, Python25Mapper, UnmanagedDataMarker
from Ironclad.Structs import PyObject, PyTypeObject
from IronPython.Hosting import PythonEngine


class Python25MapperTest(unittest.TestCase):

    def testBasicStoreRetrieveFree(self):
        frees = []
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)
        
        try:
            obj1 = object()
            self.assertEquals(allocs, [], "unexpected allocations")
            ptr = mapper.Store(obj1)
            self.assertEquals(len(allocs), 1, "unexpected number of allocations")
            self.assertEquals(allocs[0], (ptr, Marshal.SizeOf(PyObject)), "unexpected result")
            self.assertNotEquals(ptr, IntPtr.Zero, "did not store reference")
            self.assertEquals(mapper.RefCount(ptr), 1, "unexpected refcount")
            typePtr = CPyMarshal.ReadPtr(
                CPyMarshal.Offset(ptr, Marshal.OffsetOf(PyObject, "ob_type")))
            self.assertEquals(typePtr, mapper.PyBaseObject_Type, "opaque pointer had wrong type")

            obj2 = mapper.Retrieve(ptr)
            self.assertTrue(obj1 is obj2, "retrieved wrong object")

            self.assertEquals(frees, [], "unexpected deallocations")
            mapper.PyObject_Free(ptr)
            self.assertEquals(frees, [ptr], "unexpected deallocations")
            self.assertRaises(KeyError, lambda: mapper.RefCount(ptr))
            self.assertRaises(KeyError, lambda: mapper.Retrieve(ptr))
            self.assertRaises(KeyError, lambda: mapper.PyObject_Free(ptr))
        finally:
            deallocTypes()


    def testCanFreeWithRefCount0(self):
        frees = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator([], frees))
        
        objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        CPyMarshal.WriteInt(OffsetPtr(objPtr, Marshal.OffsetOf(PyObject, "ob_refcnt")), 0)
        mapper.StoreUnmanagedData(objPtr, object())
        mapper.PyObject_Free(objPtr)
        self.assertEquals(frees, [objPtr], "didn't actually release memory")
        

    def testStoreSameObjectIncRefsOriginal(self):
        frees = []
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, frees))
        
        obj1 = object()
        result1 = mapper.Store(obj1)
        result2 = mapper.Store(obj1)
        
        self.assertEquals(allocs, [(result1, Marshal.SizeOf(PyObject))], "unexpected result")
        self.assertEquals(result1, result2, "did not return same ptr")
        self.assertEquals(mapper.RefCount(result1), 2, "did not incref")
        
        mapper.DecRef(result1)
        mapper.DecRef(result1)
        
        self.assertEquals(frees, [result1], "did not free memory")
        
        result3 = mapper.Store(obj1)
        self.assertEquals(allocs, 
                          [(result1, Marshal.SizeOf(PyObject)), (result3, Marshal.SizeOf(PyObject))], 
                          "unexpected result -- failed to clear reverse mapping?")
        mapper.DecRef(result3)
        

    def testStoreEqualObjectStoresSeparately(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        result1 = mapper.Store([1, 2, 3])
        result2 = mapper.Store([1, 2, 3])
        
        self.assertNotEquals(result1, result2, "confused seoparate objects")
        self.assertEquals(mapper.RefCount(result1), 1, "wrong")
        self.assertEquals(mapper.RefCount(result2), 1, "wrong")
        
        mapper.DecRef(result1)
        mapper.DecRef(result2)


    def testDecRefObjectWithZeroRefCountFails(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        CPyMarshal.WriteInt(OffsetPtr(objPtr, Marshal.OffsetOf(PyObject, "ob_refcnt")), 0)
        mapper.StoreUnmanagedData(objPtr, object())
        self.assertRaises(BadRefCountException, lambda: mapper.DecRef(objPtr))
        Marshal.FreeHGlobal(objPtr)


    def testFinalDecRefOfObjectWithTypeCalls_tp_dealloc(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        calls = []
        def TypeDealloc(ptr):
            calls.append(ptr)
        deallocDgt = CPython_destructor_Delegate(TypeDealloc)
        deallocFP = Marshal.GetFunctionPointerForDelegate(deallocDgt)
        
        typePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        deallocPtr = CPyMarshal.Offset(typePtr, Marshal.OffsetOf(PyTypeObject, "tp_dealloc"))
        CPyMarshal.WritePtr(deallocPtr, deallocFP)
        
        obj = object()
        objPtr = mapper.Store(obj)
        objTypePtr = CPyMarshal.Offset(objPtr, Marshal.OffsetOf(PyObject, "ob_type"))
        CPyMarshal.WritePtr(objTypePtr, typePtr)
        
        mapper.IncRef(objPtr)
        mapper.DecRef(objPtr)
        self.assertEquals(calls, [], "called prematurely")
        mapper.DecRef(objPtr)
        self.assertEquals(calls, [objPtr], "not called when refcount hit 0")
    
    
    def testFinalDecRefDoesNotCallNull_tp_dealloc_ButDoesFreeMemory(self):
        frees = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator([], frees))
        
        typePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        deallocPtr = CPyMarshal.Offset(typePtr, Marshal.OffsetOf(PyTypeObject, "tp_dealloc"))
        CPyMarshal.WritePtr(deallocPtr, IntPtr.Zero)
        
        obj = object()
        objPtr = mapper.Store(obj)
        objTypePtr = CPyMarshal.Offset(objPtr, Marshal.OffsetOf(PyObject, "ob_type"))
        CPyMarshal.WritePtr(objTypePtr, typePtr)
        
        mapper.IncRef(objPtr)
        mapper.DecRef(objPtr)
        self.assertEquals(frees, [], "freed prematurely")
        mapper.DecRef(objPtr)
        self.assertEquals(frees, [objPtr], "not freed when refcount hit 0")
    

    def testStoreUnmanagedData(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)

        o = object()
        ptr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        mapper.StoreUnmanagedData(ptr, o)

        self.assertEquals(mapper.Retrieve(ptr), o, "object not stored")
        self.assertEquals(mapper.Store(o), ptr, "object not reverse-mapped")


    def testCannotStoreUnmanagedDataMarker(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.PyStringObject))
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.PyTupleObject))


    def testRefCountIncRefDecRef(self):
        frees = []
        engine = PythonEngine()
        allocator = GetAllocatingTestAllocator([], frees)
        mapper = Python25Mapper(engine, allocator)

        obj1 = object()
        ptr = mapper.Store(obj1)
        mapper.IncRef(ptr)
        self.assertEquals(mapper.RefCount(ptr), 2, "unexpected refcount")

        mapper.DecRef(ptr)
        self.assertEquals(mapper.RefCount(ptr), 1, "unexpected refcount")

        self.assertEquals(frees, [], "unexpected deallocations")
        mapper.DecRef(ptr)
        self.assertEquals(frees, [ptr], "unexpected deallocations")
        self.assertRaises(KeyError, lambda: mapper.Retrieve(ptr))
        self.assertRaises(KeyError, lambda: mapper.PyObject_Free(ptr))
        self.assertRaises(KeyError, lambda: mapper.RefCount(IntPtr(1)))


    def testNullPointers(self):
        engine = PythonEngine()
        allocator = GetDoNothingTestAllocator([])
        mapper = Python25Mapper(engine, allocator)

        self.assertRaises(KeyError, lambda: mapper.IncRef(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.DecRef(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.Retrieve(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.PyObject_Free(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.RefCount(IntPtr.Zero))


    def testRememberAndFreeTempPtrs(self):
        # hopefully, nobody will depend on character data from PyArg_Parse* remaining
        # available beyond the function call in which it was provided. hopefully.
        frees = []
        engine = PythonEngine()
        allocator = GetDoNothingTestAllocator(frees)
        mapper = Python25Mapper(engine, allocator)

        mapper.RememberTempPtr(IntPtr(12345))
        mapper.RememberTempPtr(IntPtr(13579))
        mapper.RememberTempPtr(IntPtr(56789))
        self.assertEquals(frees, [], "freed memory prematurely")

        mapper.FreeTemps()
        self.assertEquals(set(frees), set([IntPtr(12345), IntPtr(13579), IntPtr(56789)]),
                          "memory not freed")


    def testRememberAndFreeTempObjects(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)

        tempObject1 = mapper.Store(1)
        tempObject2 = mapper.Store(2)

        mapper.RememberTempObject(tempObject1)
        mapper.RememberTempObject(tempObject2)

        self.assertEquals(mapper.RefCount(tempObject1), 1,
                          "RememberTempObject should not incref")
        self.assertEquals(mapper.RefCount(tempObject2), 1,
                          "RememberTempObject should not incref")

        mapper.IncRef(tempObject1)
        mapper.IncRef(tempObject2)

        mapper.FreeTemps()

        try:
            self.assertEquals(mapper.RefCount(tempObject1), 1,
                              "FreeTemps should decref objects rather than freeing them")
            self.assertEquals(mapper.RefCount(tempObject2), 1,
                              "FreeTemps should decref objects rather than freeing them")

            mapper.FreeTemps()
            self.assertEquals(mapper.RefCount(tempObject1), 1,
                              "FreeTemps should clear list once called")
            self.assertEquals(mapper.RefCount(tempObject2), 1,
                              "FreeTemps should clear list once called")
        finally:
            mapper.DecRef(tempObject1)
            mapper.DecRef(tempObject2)
    

class Python25Mapper_GetMethodFP_Test(unittest.TestCase):
    
    def assertGetMethodFPWorks(self, name):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        fp1 = mapper.GetMethodFP(name)
        fp2 = mapper.GetMethodFP(name)
        self.assertEquals(fp1, fp2, "did not remember func ptrs")
        
    
    def testMethods(self):
        methods = (
            "PyBaseObject_Dealloc",
            "PyTuple_Dealloc"
        )
        for method in methods:
            self.assertGetMethodFPWorks(method)

    
class Python25Mapper_NoneTest(unittest.TestCase):
    
    def testFillNone(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        nonePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        mapper.Fill__Py_NoneStruct(nonePtr)
        noneStruct = Marshal.PtrToStructure(nonePtr, PyObject)
        self.assertEquals(noneStruct.ob_refcnt, 1, "bad refcount")
        self.assertEquals(noneStruct.ob_type, IntPtr.Zero, "unexpected type")
        Marshal.FreeHGlobal(nonePtr)
    
    
    def testStoreNone(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        nonePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        mapper.SetData("_Py_NoneStruct", nonePtr)
        
        # if the following line fails, we probably have a public Store overload taking something
        # more specific than 'object', which is therefore called in preference to the 'object'
        # version of Store. (IronPython None becomes C# null, which is of every type. Sort of.)
        resultPtr = mapper.Store(None)
        self.assertEquals(resultPtr, nonePtr, "wrong")
        self.assertEquals(mapper.RefCount(nonePtr), 2, "did not incref")
        
        self.assertEquals(mapper.Retrieve(nonePtr), None, "not mapped properly")

        Marshal.FreeHGlobal(nonePtr)
    

class Python25Mapper_PyInt_FromLong_Test(unittest.TestCase):
    
    def testPyInt_FromLong(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        for value in (0, 2147483647, -2147483648):
            ptr = mapper.PyInt_FromLong(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            mapper.DecRef(ptr)


class Python25Mapper_PyInt_FromSsize_t_Test(unittest.TestCase):
    
    def testPyInt_FromSsize_t(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        for value in (0, 2147483647, -2147483648):
            ptr = mapper.PyInt_FromSsize_t(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            mapper.DecRef(ptr)


class Python25Mapper_PyFloat_FromDouble_Test(unittest.TestCase):
    
    def testPyFloat_FromDouble(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        for value in (0.0, 3.3e33, -3.3e-33):
            ptr = mapper.PyFloat_FromDouble(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            mapper.DecRef(ptr)



suite = makesuite(
    Python25MapperTest,
    Python25Mapper_GetMethodFP_Test,
    Python25Mapper_NoneTest,
    Python25Mapper_PyInt_FromLong_Test,
    Python25Mapper_PyInt_FromSsize_t_Test,
    Python25Mapper_PyFloat_FromDouble_Test,
)

if __name__ == '__main__':
    run(suite)