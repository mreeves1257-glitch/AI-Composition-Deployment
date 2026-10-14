#!/usr/bin/env python3
"""Run full Composer regressions and independently count Classical test cases."""
import argparse, importlib.util, json, os, subprocess, sys, unittest
from pathlib import Path

def run_unittest_discovery(root):
    env=os.environ.copy()
    env["PYTHONPATH"]=str(root)+os.pathsep+env.get("PYTHONPATH","")
    p=subprocess.run([sys.executable,"-m","unittest","discover","-v",str(root)],
                     text=True,capture_output=True,env=env)
    return {"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr}

def load_suite_from_file(path, root):
    name="recovery_test_"+str(abs(hash(str(path))))
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError("LOAD_SPEC_FAILED:"+str(path))
    mod=importlib.util.module_from_spec(spec)
    old=sys.path[:]
    sys.path.insert(0,str(path.parent)); sys.path.insert(0,str(root))
    try: spec.loader.exec_module(mod)
    finally: sys.path[:]=old
    return unittest.defaultTestLoader.loadTestsFromModule(mod)

def iter_cases(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite): yield from iter_cases(item)
        else: yield item

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("working_copy",type=Path)
    ap.add_argument("output",type=Path)
    a=ap.parse_args(); root=a.working_copy.resolve()
    test_files=list(root.rglob("test_*.py"))
    classical=[]; load_errors=[]
    for p in test_files:
        source=p.read_text(errors="ignore")
        if "classical" in p.name.lower() or ("Classical" in source and "unittest" in source):
            try:
                suite=load_suite_from_file(p,root)
                cases=list(iter_cases(suite))
                if cases: classical.extend((p,c) for c in cases)
            except Exception as e:
                load_errors.append({"file":str(p.relative_to(root)),"error":repr(e)})
    unique={}
    for p,c in classical: unique[c.id()]={"file":str(p.relative_to(root)),"id":c.id()}
    if load_errors: raise SystemExit("CLASSICAL_TEST_LOAD_ERRORS:"+json.dumps(load_errors))
    if len(unique)!=43: raise SystemExit(f"CLASSICAL_TEST_COUNT_MISMATCH:{len(unique)}:EXPECTED_43")
    suite=unittest.TestSuite(); wanted=set(unique)
    for p in sorted({p for p,_ in classical}):
        s=load_suite_from_file(p,root)
        suite.addTests([c for c in iter_cases(s) if c.id() in wanted])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not (result.wasSuccessful() and result.testsRun==43): raise SystemExit("CLASSICAL_43_FAILED")
    full=run_unittest_discovery(root)
    if full["returncode"]!=0: raise SystemExit("FULL_UNITTEST_REGRESSION_FAILED\n"+full["stdout"]+"\n"+full["stderr"])
    report={"status":"PASS","classical":{"tests_run":result.testsRun,"expected":43,"status":"PASS",
            "test_ids":list(unique.values())},
            "full_unittest":{"status":"PASS","stdout":full["stdout"],"stderr":full["stderr"]}}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":"PASS","classical":43,"full_unittest":"PASS"},indent=2))
if __name__=="__main__": main()
