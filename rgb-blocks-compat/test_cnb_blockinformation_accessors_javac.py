#!/usr/bin/env python3
"""Compile the ACTUAL RGB C&B-source statistics reader on Java 17 and 21.

Regression for 1.20.1 Forge: Chisels & Bits IBlockInformation exposes
getBlockState(), not the 1.21.1 BlockInformation record's blockState().
The old reader silently ignored the former, so 4095 real Glow microbits
gave a ZERO RGB C&B source. This test extracts the production methods and
accumulator directly; never reimplements the bridge in Python.
"""
from pathlib import Path
import subprocess
import tempfile

path=Path("rgb-blocks-compat/recovered/fabric/com/rgbblocks/client/lighting/RGBRealLightEngine.java")
production=path.read_text(encoding="utf-8")

def extract(signature):
    start=production.find(signature)
    assert start>=0,("Missing production C&B RGB source method",signature)
    opening=production.find("{",start)
    assert opening>=0,("Missing Java opening brace",signature)
    depth=0
    for cursor in range(opening,len(production)):
        if production[cursor]=="{":depth+=1
        elif production[cursor]=="}":
            depth-=1
            if depth==0:return production[start:cursor+1]
    raise AssertionError(("Unbalanced source Java braces",signature))

methods=[
    extract("private static RGBRealLightEngine.CnbSource computeCnbSourceFromAccessor("),
    extract("private static RGBRealLightEngine.CnbSource computeCnbSourceFromStatistics("),
    extract("private static void addCnbInformation("),
    extract("private static Object invokeNoArg("),
    extract("private static final class CnbAccumulator"),
    extract("private record CnbSource("),
]
bridge=methods[2]
assert 'invokeNoArg(information, "blockState")' in bridge
assert 'invokeNoArg(information, "getBlockState")' in bridge
assert "catch (NoSuchMethodException olderCnbApi)" in bridge
assert bridge.index('invokeNoArg(information, "blockState")') < bridge.index(
    'invokeNoArg(information, "getBlockState")')

java=r'''import java.util.*;
import java.util.Map.Entry;
import java.util.stream.Stream;
import java.lang.reflect.Method;

public final class RGBRealLightEngine {
   static final class BlockState {
      final int rgb;
      BlockState(int color){rgb=color;}
   }
   static class ForgeOldInformation {
      final BlockState state;
      ForgeOldInformation(BlockState state){this.state=state;}
      public BlockState getBlockState(){return state;}
   }
   static class NeoRecordInformation {
      final BlockState state;
      NeoRecordInformation(BlockState state){this.state=state;}
      public BlockState blockState(){return state;}
   }
   static class ParentInformation {
      final BlockState state;
      ParentInformation(BlockState state){this.state=state;}
      protected BlockState getBlockState(){return state;}
   }
   static class InheritedForgeInformation extends ParentInformation {
      InheritedForgeInformation(BlockState state){super(state);}
   }
   static class UnsupportedInformation { public String unknown(){return "?";} }
   static class Statistics {
      final Map<Object,Integer> counts;
      Statistics(Map<Object,Integer> counts){this.counts=counts;}
      public Map<Object,Integer> getStateCounts(){return counts;}
   }
   static class ChiseledBlockEntity {
      final Statistics statistics;
      ChiseledBlockEntity(Map<Object,Integer> states){
          statistics=new Statistics(states);
      }
      public Statistics getStatistics(){return statistics;}
   }

   static int rgbForState(BlockState state){return state.rgb;}
   static float clamp(float value,float low,float high){
      return value<low?low:Math.min(value,high);
   }
   static int clamp255(int value){return Math.max(0,Math.min(255,value));}
   static boolean implementsCnbAccessor(Class<?> type){return false;}
   /* EXACT_PRODUCTION_METHODS */

   static void require(boolean result,String message){
      if(!result)throw new AssertionError(message);
   }
   static CnbSource from(Object info,int bits) {
      return computeCnbSourceFromAccessor(
          new ChiseledBlockEntity(Map.of(info,bits)));
   }
   public static void main(String[] args){
      BlockState green=new BlockState(0x3bd119);
      BlockState blue=new BlockState(0x0855d1);
      BlockState air=new BlockState(-1);
      // The exact 1.20.1 bug: one real C&B Glow sculpture consists of
      // 4,095 green pixels, yet old RGB ignored Forge's getBlockState().
      CnbSource forge=from(new ForgeOldInformation(green),4095);
      require(forge.active(),"Forge C&B 4095 green Glow voxels emitted ZERO light");
      require(forge.rgb()==0x49ff1f || forge.rgb()!=0,"Forge RGB emitter stayed BLACK");
      require(forge.energy()>=0.66f,"Forge recovered emission is unexpectedly weak");
      // 1.21.1 record accessor must retain its existing color path.
      CnbSource neo=from(new NeoRecordInformation(blue),4095);
      require(neo.active(),"NeoForge 1.21.1 C&B record lost Glow emission");
      require(neo.rgb()!=forge.rgb(),"Different blue/green source colors collapsed");
      // Both old and new C&B information implementations in one sculpture.
      Map<Object,Integer> mixed=new LinkedHashMap<>();
      mixed.put(new ForgeOldInformation(green),2048);
      mixed.put(new NeoRecordInformation(blue),2047);
      CnbSource blend=computeCnbSourceFromStatistics(new ChiseledBlockEntity(mixed));
      require(blend.active(),"Mixed two-version material style did not emit");
      require(blend.rgb()!=neo.rgb()&&blend.rgb()!=forge.rgb(),
              "Mixed C&B material colors failed to blend");
      // Inherited non-public API belongs to the old reflective code path.
      CnbSource inherited=from(new InheritedForgeInformation(green),4095);
      require(inherited.active(),"Inherited protected Forge getter inaccessible");
      // A chiseled non-emitter must NOT become a ghost light source.
      CnbSource plain=from(new ForgeOldInformation(air),4095);
      require(!plain.active(),"Ordinary C&B AIR/non-emitter created ghost RGB");
      CnbSource unrecognized=from(new UnsupportedInformation(),4095);
      require(!unrecognized.active(),"Unknown C&B representation created fake glow");
      CnbSource empty=from(new ForgeOldInformation(green),0);
      require(!empty.active(),"Zero real Glow bits generated RGB emission");
      System.out.println("RGB_PORT_CNB_MATERIAL_API_REAL_JAVAC_PASS"+
          " forge_1201_getBlockState=true neoforge_1211_blockState=true"+
          " mixed_rgb=true inherited_old_api=true nonemitter_black=true");
   }
}'''
java=java.replace("/* EXACT_PRODUCTION_METHODS */","\n".join(methods))
for ver in ("17","21"):
    with tempfile.TemporaryDirectory(prefix="rgb-cnb-info-"+ver+"-") as temp:
        file=Path(temp)/"RGBRealLightEngine.java"
        file.write_text(java,encoding="utf-8")
        compile=subprocess.run(["javac","--release",ver,"-encoding","UTF-8",
                                "-d",temp,str(file)],
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=45)
        if compile.returncode:
            raise RuntimeError("Production RGB C&B API Java"+ver+
                               " failed javac:\n"+compile.stdout[-6500:])
        result=subprocess.run(["java","-cp",temp,"RGBRealLightEngine"],
             stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30)
        if result.returncode:
            raise RuntimeError("Production RGB C&B API Java"+ver+
                               " failed execution:\n"+result.stdout[-6500:])
        assert "RGB_PORT_CNB_MATERIAL_API_REAL_JAVAC_PASS" in result.stdout
        print("JAVA "+ver+" "+result.stdout.strip(),flush=True)
