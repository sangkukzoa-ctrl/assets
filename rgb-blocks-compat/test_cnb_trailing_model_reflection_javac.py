#!/usr/bin/env python3
"""Compile the production C&B trailing mesh update method on Java 17/21.

The last delayed C&B mesh rebuild must survive non-public native entity
implementations and inherited protected updateModelData(). Reflectively
invoking only Class#getMethod() lost valid non-public callbacks.
"""
from pathlib import Path
import subprocess,tempfile

path=Path("rgb-blocks-compat/recovered/fabric/com/rgbblocks/client/cnb/RGBCnbGeometryBakeDebouncer.java")
production=path.read_text("utf-8")

def extract(signature):
    start=production.find(signature)
    assert start>=0,("Production C&B trailing method missing",signature)
    begin=production.index("{",start)
    depth=0
    for cursor in range(begin,len(production)):
        if production[cursor]=="{":depth+=1
        elif production[cursor]=="}":
            depth-=1
            if depth==0:return production[start:cursor+1]
    raise AssertionError("Unbalanced production Java helper")

source=extract("private static Method findModelUpdateMethod(")
assert 'getMethod("updateModelData")' in source
assert 'getDeclaredMethod("updateModelData")' in source
assert "setAccessible(true)" in source
assert "getSuperclass()" in source
assert "findModelUpdateMethod(live.getClass())" in production
assert "runUndebounced(() -> {" in production
assert "entry.requestSerial.get() != serial" in production
assert "epoch != WORLD_EPOCH.get()" in production

java=r'''import java.lang.reflect.Method;
public final class CnbTrailingModelAccessTest {
   static class PublicTile {
      int updates;
      public void updateModelData(){updates++;}
   }
   static class ProtectedParent {
      int updates;
      protected void updateModelData(){updates++;}
   }
   static class ForgeInheritedTile extends ProtectedParent {}
   private static class PrivateNeoTile {
      int updates;
      private void updateModelData(){updates++;}
   }
   static class NoModelData {}
   /* ACTUAL_MODEL_METHOD */
   private static void test(Object tile)throws Exception{
      Method method=findModelUpdateMethod(tile.getClass());
      method.invoke(tile);
   }
   private static void require(boolean condition,String message){
      if(!condition)throw new AssertionError(message);
   }
   public static void main(String[] args)throws Exception {
      PublicTile publicTile=new PublicTile();
      test(publicTile);require(publicTile.updates==1,"Public native model callback missed");
      ForgeInheritedTile inheritedTile=new ForgeInheritedTile();
      test(inheritedTile);require(inheritedTile.updates==1,
          "Inherited protected old C&B callback failed");
      PrivateNeoTile privateTile=new PrivateNeoTile();
      test(privateTile);require(privateTile.updates==1,
          "Nonpublic C&B entity method was inaccessible");
      boolean missingRejected=false;
      try{findModelUpdateMethod(NoModelData.class);}
      catch(NoSuchMethodException valid){missingRejected=true;}
      require(missingRejected,"Missing C&B API erroneously succeeded");
      System.out.println("RGB_PORT_CNB_TRAILING_MESH_REFLECTION_PASS"+
          " public=true inherited_protected=true nonpublic=true"+
          " missing_api_reported=true");
   }
}'''.replace("/* ACTUAL_MODEL_METHOD */",source)
with tempfile.TemporaryDirectory(prefix="rgb-cnb-trailing-") as temp:
    file=Path(temp)/"CnbTrailingModelAccessTest.java"
    file.write_text(java,encoding="utf-8")
    for ver in ("17","21"):
        out=Path(temp)/ver
        out.mkdir()
        build=subprocess.run(["javac","--release",ver,"-encoding","UTF-8",
                              "-d",str(out),str(file)],capture_output=True,
                              text=True,timeout=30)
        if build.returncode:
            raise RuntimeError("Actual C&B trailing method failed javac "+ver+
                               ":\n"+build.stderr[-6500:])
        run=subprocess.run(["java","-cp",str(out),"CnbTrailingModelAccessTest"],
                           capture_output=True,text=True,timeout=20)
        if run.returncode:
            raise RuntimeError("Actual C&B trailing method failed Java "+ver+
                               ":\n"+run.stdout[-6000:]+run.stderr[-6000:])
        assert "RGB_PORT_CNB_TRAILING_MESH_REFLECTION_PASS" in run.stdout
        print("JAVA "+ver+" "+run.stdout.strip(),flush=True)
