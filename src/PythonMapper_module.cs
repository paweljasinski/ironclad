using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

using IronPython.Hosting;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Hosting.Providers;
using Microsoft.Scripting.Runtime;

namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        public override IntPtr 
        Py_InitModule4(string name, IntPtr methodsPtr, string doc, IntPtr selfPtr, int apiver)
        {
            name = this.FixImportName(name);
            
            PythonDictionary methodTable = new PythonDictionary();
            PythonModule module = new PythonModule();
            this.AddModule(name, module);
            this.CreateModulesContaining(name);

            PythonDictionary __dict__ = module.__dict__;
            __dict__["__doc__"] = doc;
            __dict__["__name__"] = name;
            string __file__ = this.importFiles.Peek();
            __dict__["__file__"] = __file__;
            List __path__ = new List();
            if (__file__ != null)
            {
                __path__.append(Path.GetDirectoryName(__file__));
            }
            __dict__["__path__"] = __path__;
            __dict__["_dispatcher"] = new Dispatcher(this, methodTable, selfPtr);

            StringBuilder moduleCode = new StringBuilder();
            moduleCode.Append(CodeSnippets.USEFUL_IMPORTS);
            CallableBuilder.GenerateFunctions(moduleCode, methodsPtr, methodTable);
            this.ExecInModule(moduleCode.ToString(), module);
            
            return this.Store(module);
        }
        
        public override IntPtr
        PyEval_GetBuiltins()
        {
            PythonModule __builtin__ = this.GetModule("__builtin__");
            return this.Store(__builtin__.__dict__);
        }
        
        public override IntPtr
        PySys_GetObject(string name)
        {
            try
            {
                return this.Store(this.python.SystemState.__dict__[name]);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override IntPtr
        PyModule_New(string name)
        {
            PythonModule module = new PythonModule();
            module.__dict__["__name__"] = name;
            module.__dict__["__doc__"] = "";
            return this.Store(module);
        }

        public override IntPtr
        PyModule_GetDict(IntPtr modulePtr)
        {
            PythonModule module = (PythonModule)this.Retrieve(modulePtr);
            return this.Store(module.__dict__);
        }

        private int 
        IC_PyModule_Add(IntPtr modulePtr, string name, object value)
        {
            if (!this.map.HasPtr(modulePtr))
            {
                return -1;
            }
            PythonModule module = (PythonModule)this.Retrieve(modulePtr);
            module.__setattr__(name, value);
            return 0;
        }
        
        public override int 
        PyModule_AddObject(IntPtr modulePtr, string name, IntPtr valuePtr)
        {
            if (!this.map.HasPtr(modulePtr))
            {
                return -1;
            }
            object value = this.Retrieve(valuePtr);
            this.DecRef(valuePtr);
            return this.IC_PyModule_Add(modulePtr, name, value);
        }
        
        public override int
        PyModule_AddIntConstant(IntPtr modulePtr, string name, int value)
        {
            return this.IC_PyModule_Add(modulePtr, name, value);
        }
        
        public override int
        PyModule_AddStringConstant(IntPtr modulePtr, string name, string value)
        {
            return this.IC_PyModule_Add(modulePtr, name, value);
        }

        private void
        ExecInModule(string code, PythonModule module)
        {
            SourceUnit script = this.python.CreateSnippet(code, SourceCodeKind.Statements);
            script.Execute(new Scope(module.__dict__));
        }
        
        public void
        AddModule(string name, PythonModule module)
        {
            PythonDictionary modules = (PythonDictionary)this.python.SystemState.__dict__["modules"];
            modules[name] = module;
        }

        public PythonModule
        GetModule(string name)
        {
            PythonDictionary modules = (PythonDictionary)this.python.SystemState.__dict__["modules"];
            if (modules.has_key(name))
            {
                return (PythonModule)modules[name];
            }
            return null;
        }
        
        private void
        CreateScratchModule()
        {
            this.scratchModule = new PythonModule();
            this.scratchModule.__dict__["_mapper"] = this;

            this.ExecInModule(CodeSnippets.USEFUL_IMPORTS, this.scratchModule);
            this.scratchContext = new ModuleContext(this.scratchModule.__dict__, this.python).GlobalContext;
        }
    }
}