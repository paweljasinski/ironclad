
import os
import shutil
import tempfile
from tests.utils.process import spawn
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

def write(name, text):
    f = open(name, 'w')
    try:
        f.write(text)
    finally:
        f.close()

def read(name):
    f = open(name)
    try:
        return f.read()
    finally:
        f.close()


class GeneratePython25MapperTest(TestCase):

    def testCreatesPython25MapperComponents(self):
        tempDir = tempfile.mkdtemp()
        testBuildDir = os.path.join(tempDir, 'generatepython25mappertest')
        if os.path.exists(testBuildDir):
            shutil.rmtree(testBuildDir)
        os.mkdir(testBuildDir)
        testSrcDir = os.path.join(testBuildDir, 'python25mapper_components')
        os.mkdir(testSrcDir)

        origCwd = os.getcwd()
        toolPath = os.path.join(origCwd, "tools/generatepython25mapper.py")

        os.chdir(testSrcDir)
        try:
            write("exceptions", EXCEPTIONS)
            write("builtin_exceptions", BUILTIN_EXCEPTIONS)
            write("store", STORE)
            write("numbers_pythonsites", NUMBERS_PYTHONSITES)

            retVal = spawn("ipy", toolPath)
            self.assertEquals(retVal, 0, "process ended badly")

            os.chdir(testBuildDir)
            self.assertEquals(read("Python25Mapper_exceptions.Generated.cs"), EXPECTED_EXCEPTIONS, 
                              "generated exceptions wrong")
            self.assertEquals(read("Python25Mapper_builtin_exceptions.Generated.cs"), EXPECTED_BUILTIN_EXCEPTIONS, 
                              "generated builtin exceptions wrong")
            self.assertEquals(read("Python25Mapper_store.Generated.cs"), EXPECTED_STORE, 
                              "generated wrong")
            self.assertEquals(read("Python25Mapper_numbers_PythonSites.Generated.cs"), EXPECTED_NUMBERS_PYTHONSITES, 
                              "generated wrong")

        finally:
            os.chdir(origCwd)
        shutil.rmtree(tempDir)

USINGS = """
using System;
using System.Collections;
using IronPython.Runtime;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;
using Microsoft.Scripting.Math;
"""

EXCEPTIONS = """
SystemError
OverflowError
"""

EXPECTED_EXCEPTIONS = USINGS + """
namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override IntPtr Make_PyExc_SystemError()
        {
            return this.Store(PythonExceptions.SystemError);
        }

        public override IntPtr Make_PyExc_OverflowError()
        {
            return this.Store(PythonExceptions.OverflowError);
        }
    }
}
"""

BUILTIN_EXCEPTIONS = """
BaseException
WindowsError
"""

EXPECTED_BUILTIN_EXCEPTIONS = USINGS + """
namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override IntPtr Make_PyExc_BaseException()
        {
            return this.Store(Builtin.BaseException);
        }

        public override IntPtr Make_PyExc_WindowsError()
        {
            return this.Store(Builtin.WindowsError);
        }
    }
}
"""

STORE = """
string
Tuple
Dict
"""

EXPECTED_STORE = USINGS + """
namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        private IntPtr StoreDispatch(object obj)
        {
            if (obj is string) { return this.Store((string)obj); }
            if (obj is Tuple) { return this.Store((Tuple)obj); }
            if (obj is Dict) { return this.Store((Dict)obj); }
            return this.StoreObject(obj);
        }
    }
}
"""
NUMBERS_PYTHONSITES = """
PyNumber_Add Add
PyNumber_Remainder Mod
"""
EXPECTED_NUMBERS_PYTHONSITES = USINGS + """
namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override IntPtr
        PyNumber_Add(IntPtr arg1ptr, IntPtr arg2ptr)
        {
            try
            {
                object result = PythonSites.Add(this.Retrieve(arg1ptr), this.Retrieve(arg2ptr));
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override IntPtr
        PyNumber_Remainder(IntPtr arg1ptr, IntPtr arg2ptr)
        {
            try
            {
                object result = PythonSites.Mod(this.Retrieve(arg1ptr), this.Retrieve(arg2ptr));
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
    }
}
"""

suite = makesuite(GeneratePython25MapperTest)

if __name__ == '__main__':
    run(suite)