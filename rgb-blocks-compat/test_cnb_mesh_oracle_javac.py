#!/usr/bin/env python3
"""Compile/run the EXACT production C&B voxel-presence methods without Minecraft.

No original author archive or external mod needed. Extract real Java method
bodies from RGB's port mesh watchdog; surround them with minimal test stubs.
This checks the actual Forge getBlockState(), NeoForge blockState(), empty
C&B AIR-only sculpture, and reflection on protected inherited API methods.
"""
from pathlib import Path
import subprocess, tempfile

SOURCE=Path("rgb-blocks-compat/recovered/fabric/com/rgbblocks/client/cnb/RGBCnbMeshIntegrity.java")
source=SOURCE.read_text("utf-8")

def method_body(declaration):
    at=source.find(declaration)
    if at<0:raise AssertionError("Production C&B mesh method vanished: "+declaration)
    start=source.find("{",at)
    if start<0:raise AssertionError("No Java body: "+declaration)
    depth=0
    for i in range(start,len(source)):
        if source[i]=="{":depth+=1
        elif source[i]=="}":
            depth-=1
            if depth==0:return source[at:i+1]
    raise AssertionError("Unbalanced production Java method "+declaration)

real_methods=[
    method_body("private static boolean hasActualVoxelStates("),
    method_body("private static Method findZeroArg("),
]
assert "information instanceof BlockState direct" in real_methods[0]
assert "!state.isAir()" in real_methods[0]
assert 'findZeroArg(information.getClass(),"blockState")' in real_methods[0]
assert 'findZeroArg(information.getClass(),"getBlockState")' in real_methods[0]

java=r'''import java.util.Map;
import java.util.LinkedHashMap;
import java.lang.reflect.Method;
public final class CnbVoxelAirGuardTest {
  static final class BlockState {
    private final boolean air;
    BlockState(boolean air){this.air=air;}
    public boolean isAir(){return air;}
  }
  static class BlockEntity {
    private final Stats stats;
    BlockEntity(Map<Object,Integer> counts){this.stats=new Stats(counts);}
    public Stats getStatistics(){return stats;}
  }
  static class Stats {
    private final Map<Object,Integer> counts;
    Stats(Map<Object,Integer> counts){this.counts=counts;}
    public Map<Object,Integer> getStateCounts(){return counts;}
  }
  static class NeoInformation {
    private final BlockState state;
    NeoInformation(BlockState s){this.state=s;}
    public BlockState blockState(){return state;}
  }
  static class ForgeInformation {
    private final BlockState state;
    ForgeInformation(BlockState s){this.state=s;}
    public BlockState getBlockState(){return state;}
  }
  static class ParentInformation {
    private final BlockState state;
    ParentInformation(BlockState s){this.state=s;}
    protected BlockState getBlockState(){return state;}
  }
  static class InheritedInformation extends ParentInformation {
    InheritedInformation(BlockState s){super(s);}
  }
  static class AbsentInformation {}
  /* EXACT_PRODUCTION_METHODS */
  private static void require(boolean good,String message){
    if(!good)throw new AssertionError(message);
  }
  public static void main(String[] args)throws Exception{
    var air=new BlockState(true);
    var glow=new BlockState(false);
    require(!hasActualVoxelStates(new BlockEntity(Map.of())), "empty stats");
    require(!hasActualVoxelStates(new BlockEntity(Map.of(new ForgeInformation(air),4096))),
            "AIR-only 4096 microbits resurrected an EMPTY mesh");
    require(!hasActualVoxelStates(new BlockEntity(Map.of(new NeoInformation(air),4096))),
            "Neo AIR-only sculpture marked as geometry");
    require(hasActualVoxelStates(new BlockEntity(Map.of(new ForgeInformation(glow),4095))),
            "Forge RGB microbits should trigger actual mesh verification");
    require(hasActualVoxelStates(new BlockEntity(Map.of(new NeoInformation(glow),4095))),
            "NeoForge RGB record accessor should trigger mesh verification");
    Map<Object,Integer> mixed=new LinkedHashMap<>();
    mixed.put(new NeoInformation(air),4095);
    mixed.put(new NeoInformation(glow),1);
    require(hasActualVoxelStates(new BlockEntity(mixed)),
            "Mixed air + 1 glow bit must still have visible C&B geometry");
    require(!hasActualVoxelStates(new BlockEntity(Map.of(new ForgeInformation(glow),0))),
            "Zero actual RGB microbits are not geometry");
    require(hasActualVoxelStates(new BlockEntity(Map.of(glow,1))),
            "Direct BlockState material not detected");
    require(!hasActualVoxelStates(new BlockEntity(Map.of(air,4096))),
            "Direct air material incorrectly treated as model");
    require(hasActualVoxelStates(new BlockEntity(Map.of(new InheritedInformation(glow),7))),
            "Inherited nonpublic Forge accessor should remain discoverable");
    boolean unknownRejected=false;
    try{hasActualVoxelStates(new BlockEntity(Map.of(new AbsentInformation(),2)));}
    catch(NoSuchMethodException expected){unknownRejected=true;}
    require(unknownRejected,"Unknown C&B API shape must not yield a fake PASS");
    System.out.println("RGB_PORT_CNB_MESH_REAL_JAVAC_PASS"+
      " forge_accessor=true neo_accessor=true inherited_accessor=true"+
      " air_only_not_geometry=true mixed_glow=true unknown_api_not_silenced=true");
  }
}'''
java=java.replace("/* EXACT_PRODUCTION_METHODS */","\n".join(real_methods))
with tempfile.TemporaryDirectory(prefix="rgb-cnb-mesh-java-") as tmp:
    root=Path(tmp)
    target=root/"CnbVoxelAirGuardTest.java"
    target.write_text(java,encoding="utf-8")
    compile=subprocess.run(["javac","-encoding","UTF-8","-d",tmp,str(target)],
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                          text=True,timeout=30)
    if compile.returncode:
        raise RuntimeError("ACTUAL production C&B Java compilation failed:\n"+compile.stdout[-6000:])
    run=subprocess.run(["java","-cp",tmp,"CnbVoxelAirGuardTest"],
                       stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                       text=True,timeout=20)
    if run.returncode:
        raise RuntimeError("ACTUAL C&B getter/air-only stress failed:\n"+run.stdout[-6000:])
    assert "RGB_PORT_CNB_MESH_REAL_JAVAC_PASS" in run.stdout
    print(run.stdout.strip(),flush=True)
