#!/usr/bin/env python3
"""Run the EXACT production C&B mesh watchdog against same-position tile ABA.

A repaired C&B block can be removed/rechiseled at the same coordinates while
the old 600-tick cooldown remains. A newly created entity MUST NOT inherit the
old entity's cooldown. Exercise true Java object identity, including an
AIR->stone->C&B cycle that occurs entirely BETWEEN two watchdog samples.
This is a Java production-method regression, NOT a Minecraft gameplay PASS.
"""
from pathlib import Path
import subprocess
import tempfile

FILE=Path("rgb-blocks-compat/recovered/fabric/com/rgbblocks/client/cnb/RGBCnbMeshIntegrity.java")
production=FILE.read_text(encoding="utf-8")

def method(signature):
    start=production.index(signature)
    opening=production.index("{",start)
    depth=0
    for i in range(opening,len(production)):
        if production[i]=="{":depth+=1
        elif production[i]=="}":
            depth-=1
            if depth==0:return production[start:i+1]
    raise AssertionError("Unbalanced production method: "+signature)

real_methods="\n".join((
    method("public static void reset()"),
    method("public static void check(Set<Long> candidateSources)"),
    method("private static Method findZeroArg("),
))
for token in ("OBSERVED_TILES", "observed.get()!=tile", "REPAIRED.remove(id)",
              "level.getBlockEntity(pos)","!hasActualVoxelStates(tile)",
              "if(ticks-previous<REPAIR_COOLDOWN_TICKS)continue"):
    assert token in real_methods,("Lost native mesh repair identity guard",token)

java=r'''package mod.chiselsandbits;
import java.util.*;
import java.lang.ref.WeakReference;
import java.lang.reflect.Method;

public final class CnbMeshTileABARegression {
  private static final Map<Long,Integer> MISSING=new HashMap<>();
  private static final Map<Long,Long> REPAIRED=new HashMap<>();
  private static final Map<Long,WeakReference<BlockEntity>> OBSERVED_TILES=new HashMap<>();
  private static final Map<Long,Long> LAST_ORACLE_ERROR=new HashMap<>();
  private static Level lastLevel;
  private static long ticks;
  private static int cursor;
  private static final long REPAIR_COOLDOWN_TICKS=600L;

  static final class BlockPos {
    final long packed;
    BlockPos(long n){packed=n;}
    static BlockPos of(long value){return new BlockPos(value);}
    public String toString(){return "packed:"+packed;}
  }
  static final class Block {
    final String id;
    Block(String id){this.id=id;}
  }
  static final class BlockState {
    final Block block;
    BlockState(String id){block=new Block(id);}
    Block getBlock(){return block;}
  }
  static final class Registry {
    String getKey(Block b){return b.id;}
  }
  static final class BuiltInRegistries {
    static final Registry BLOCK=new Registry();
  }
  static class BlockEntity {
    boolean removed;
    boolean geometry;
    boolean rendered;
    int repairs;
    BlockEntity(boolean geometry){this.geometry=geometry;}
    public boolean isRemoved(){return removed;}
    public void updateModelData(){repairs++;rendered=true;}
  }
  static final class Level {
    boolean loaded=true;
    BlockEntity tile;
    BlockState state=new BlockState("chiselsandbits:chiseled");
    boolean isLoaded(BlockPos p){return loaded;}
    BlockEntity getBlockEntity(BlockPos p){return tile;}
    BlockState getBlockState(BlockPos p){return state;}
  }
  static final class Minecraft {
    private static final Minecraft INSTANCE=new Minecraft();
    Level level;
    static Minecraft getInstance(){return INSTANCE;}
  }
  static final class RGBCnbGeometryBakeDebouncer {
    static void runUndebounced(Runnable runnable){runnable.run();}
  }
  static final class RGBRenderInvalidator {
    static int calls;
    static void dirtyAround(BlockPos pos,int radius){
      if(radius!=2)throw new AssertionError("Wrong rebuild radius");
      calls++;
    }
  }
  static boolean hasActualVoxelStates(BlockEntity tile){return tile.geometry;}
  static boolean hasActualRenderedQuads(BlockEntity tile){return tile.rendered;}
  static void logOracleFailure(Long id,BlockPos pos,Throwable error){
    throw new AssertionError("Production watchdog swallowed a real Java error at "+pos,error);
  }
  /* EXACT_PRODUCTION_METHODS */
  static final Set<Long> SOURCES=Set.of(123456789L);
  static void sample(){
    // The real watchdog inspects candidates every 40 client ticks.
    for(int i=0;i<40;i++)check(SOURCES);
  }
  static void samples(int count){for(int i=0;i<count;i++)sample();}
  static void require(boolean ok,String message){
    if(!ok)throw new AssertionError(message);
  }
  public static void main(String[] args){
    Minecraft minecraft=Minecraft.getInstance();
    Level world=new Level();
    minecraft.level=world;

    BlockEntity first=new BlockEntity(true);
    world.tile=first;
    samples(2);
    require(first.repairs==0,"Normal async 3-strike grace must be kept");
    sample();
    require(first.repairs==1,"Old tile must receive initial mesh rescue");
    require(REPAIRED.size()==1,"Old tile cooldown missing");

    // No AIR inspection: remove/stone/reinstall happened between two scans.
    // A new C&B tile at the SAME packed block position must repair promptly.
    BlockEntity second=new BlockEntity(true);
    world.tile=second;
    samples(2);
    require(second.repairs==0,"New tile must receive its own 3-strike grace");
    sample();
    require(second.repairs==1,
      "ABA replacement inherited the previous tile's 600-tick repair cooldown");
    require(first.repairs==1,"Old removed C&B entity was repaired after replacement");

    // Same identity MUST still be rate-limited: do not cause a bake storm.
    second.rendered=false;
    samples(3);
    require(second.repairs==1,"Same C&B tile bypassed bounded 600-tick cooldown");

    // Explicit AIR/stone between scans must also forget the old repair epoch.
    world.tile=null;
    world.state=new BlockState("minecraft:stone");
    sample();
    require(MISSING.isEmpty() && REPAIRED.isEmpty() && OBSERVED_TILES.isEmpty(),
      "Non-C&B state retained stale rescue maps");
    BlockEntity third=new BlockEntity(true);
    world.tile=third;
    world.state=new BlockState("chiselsandbits:chiseled");
    samples(3);
    require(third.repairs==1,"C&B after inspected AIR/stone failed to recover");

    // A chunk unload must not transfer a stale repair cooldown on re-entry.
    world.loaded=false;
    sample();
    require(REPAIRED.isEmpty() && OBSERVED_TILES.isEmpty(),
      "Unloaded chunks retained dead tile cooldown or observer");
    world.loaded=true;
    BlockEntity fourth=new BlockEntity(true);
    world.tile=fourth;
    samples(3);
    require(fourth.repairs==1,"New C&B tile after chunk reload cannot repair");

    // AIR-only microbits must NEVER initiate geometry repairs.
    BlockEntity fifth=new BlockEntity(false);
    world.tile=fifth;
    samples(3);
    require(fifth.repairs==0,"AIR-only C&B caused a phantom mesh");
    fifth.geometry=true; // re-chisel the SAME block entity in place
    samples(3);
    require(fifth.repairs==1,"In-place AIR-to-Glow new sculpture remained black/invisible");

    // Disconnect/reload always resets per-world tile objects and cache state.
    Level reload=new Level();
    BlockEntity afterReload=new BlockEntity(true);
    reload.tile=afterReload;
    minecraft.level=reload;
    samples(3);
    require(afterReload.repairs==1,"New world inherited previous repair throttling");
    require(OBSERVED_TILES.size()==1,"Watchdog retained tile references across worlds");

    require(RGBRenderInvalidator.calls==6,"Unexpected number of bounded repairs: "+
      RGBRenderInvalidator.calls);
    System.out.println("RGB_PORT_CNB_MESH_TILE_ABA_REAL_JAVAC_PASS"+
       " unseen_air_aba=true inspected_air_reset=true"+
       " per_entity_three_strikes=true same_tile_cooldown_preserved=true"+
       " chunk_unload_reset=true air_to_glow_in_place=true"+
       " dimension_reload_reset=true repair_calls="+RGBRenderInvalidator.calls);
  }
}
'''.replace("/* EXACT_PRODUCTION_METHODS */",real_methods)

with tempfile.TemporaryDirectory(prefix="rgb-mesh-tile-aba-") as td:
    root=Path(td)
    src=root/"CnbMeshTileABARegression.java"
    src.write_text(java,encoding="utf-8")
    for version in ("17","21"):
        dest=root/("java"+version)
        dest.mkdir()
        compile=subprocess.run(
            ["javac","--release",version,"-encoding","UTF-8","-d",str(dest),str(src)],
            capture_output=True,text=True,timeout=50)
        if compile.returncode:
            raise RuntimeError("Original mesh check Java "+version+
              " compile error:\n"+compile.stdout[-4000:]+compile.stderr[-6000:])
        run=subprocess.run(
            ["java","-cp",str(dest),"mod.chiselsandbits.CnbMeshTileABARegression"],
            capture_output=True,text=True,timeout=25)
        if run.returncode:
            raise RuntimeError("Production mesh ABA Java "+version+
              " regression failed:\n"+run.stdout[-5000:]+run.stderr[-6000:])
        assert "RGB_PORT_CNB_MESH_TILE_ABA_REAL_JAVAC_PASS" in run.stdout
        print("JAVA "+version+" "+run.stdout.strip(),flush=True)
