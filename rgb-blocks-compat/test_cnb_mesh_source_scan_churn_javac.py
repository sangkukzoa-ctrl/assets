#!/usr/bin/env python3
"""Run EXACT production C&B loaded-source watchdog scan on Java 17 and 21.

Uses a real ConcurrentHashMap.keySet, 12 keys/40-tick quota, large numbers
of long-lived RGB C&B sources, and deterministic adversarial source churn.
Also enforces disconnect immediately releases the retained old Level.
This is a Java source-extracted regression, NOT a Minecraft runtime PASS.
"""
from pathlib import Path
import subprocess
import tempfile

root=Path("rgb-blocks-compat/recovered/fabric/com/rgbblocks/client")
mesh=(root/"cnb/RGBCnbMeshIntegrity.java").read_text(encoding="utf-8")
engine=(root/"lighting/RGBRealLightEngine.java").read_text(encoding="utf-8")

def method(text,name):
    start=text.index(name)
    opening=text.index("{",start)
    nesting=0
    for i in range(opening,len(text)):
        if text[i]=="{":nesting+=1
        elif text[i]=="}":
            nesting-=1
            if nesting==0:return text[start:i+1]
    raise AssertionError("Unbalanced production Java method "+name)

real="\n".join((
    method(mesh,"public static void reset()"),
    method(mesh,"public static void check(Set<Long> candidateSources)"),
))
assert "private static Iterator<Long> candidateCursor;" in mesh
assert "candidateSources.iterator()" in real
assert "new ArrayList<>(candidateSources)" not in real, (
    "Full keySet snapshots return under large 1.3.1 C&B layouts")
assert "candidateCursor=null;" in real
assert "Math.min(12,candidateSources.size())" in real
assert "candidateCursor.next()" in real
disconnect=method(engine,"public static void onClientDisconnect()")
assert "RGBCnbMeshIntegrity.reset();" in disconnect, (
    "Disconnect still retains the prior C&B Level via static mesh watchdog")

java=r'''package com.rgbblocks.client.cnb;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.lang.ref.WeakReference;
import java.lang.reflect.Method;

public final class CnbMeshSourceScanChurnRegression {
  private static final Map<Long,Integer> MISSING=new HashMap<>();
  private static final Map<Long,Long> REPAIRED=new HashMap<>();
  private static final Map<Long,Integer> REPAIR_ATTEMPTS=new HashMap<>();
  private static final long TRANSIENT_RETRY_TICKS=160L;
  private static final int MAX_TRANSIENT_REPAIRS=3;
  private static final Map<Long,WeakReference<BlockEntity>> OBSERVED_TILES=new HashMap<>();
  private static final Map<Long,Long> LAST_ORACLE_ERROR=new HashMap<>();
  private static Level lastLevel;
  private static long ticks;
  private static Iterator<Long> candidateCursor;
  private static final long REPAIR_COOLDOWN_TICKS=600L;

  static final class BlockPos {
    final long key;
    private BlockPos(long key){this.key=key;}
    static BlockPos of(long key){return new BlockPos(key);}
  }
  static class BlockEntity {
    boolean isRemoved(){return false;}
    void updateModelData(){}
  }
  static final class Block {
    String name;
    Block(String name){this.name=name;}
  }
  static final class BlockState {
    Block getBlock(){return new Block("minecraft:air");}
  }
  static final class Registry {
    String getKey(Block block){return block.name;}
  }
  static final class BuiltInRegistries {
    static final Registry BLOCK=new Registry();
  }
  static final class Level {
    final Map<Long,AtomicInteger> visits=new ConcurrentHashMap<>();
    final AtomicInteger inspected=new AtomicInteger();
    boolean isLoaded(BlockPos pos){
      visits.computeIfAbsent(pos.key,k->new AtomicInteger()).incrementAndGet();
      inspected.incrementAndGet();
      return false; // unload is scanned, but never rebuilds inactive tiles
    }
    BlockEntity getBlockEntity(BlockPos pos){return null;}
    BlockState getBlockState(BlockPos pos){return new BlockState();}
  }
  static final class Minecraft {
    static final Minecraft INSTANCE=new Minecraft();
    Level level;
    static Minecraft getInstance(){return INSTANCE;}
  }
  static final class RGBCnbGeometryBakeDebouncer {
    static void runUndebounced(Runnable task){task.run();}
  }
  static final class RGBRenderInvalidator {
    static void dirtyAround(BlockPos pos,int radius){}
  }
  static boolean hasActualVoxelStates(BlockEntity tile){return false;}
  static boolean hasActualRenderedQuads(BlockEntity tile){return true;}
  static Method findZeroArg(Class<?> type,String name){return null;}
  static void logOracleFailure(Long key,BlockPos pos,Throwable err){
    throw new AssertionError("C&B error must not be suppressed",err);
  }
  /* INJECT_ACTUAL_PRODUCTION_METHODS */
  static void require(boolean ok,String info){
    if(!ok)throw new AssertionError(info);
  }
  static void scan(Set<Long> sources,Level level){
    int before=level.inspected.get();
    for(int tick=0;tick<40;tick++)check(sources);
    int inspected=level.inspected.get()-before;
    require(inspected<=12,"Source scan exceeded bounded quota "+inspected);
  }
  static void everyLongLivedSourceVisited(Set<Long> stable,Level level){
    for(long key:stable)require(level.visits.containsKey(key),
      "Long-lived C&B source starved under churn: "+key);
  }
  public static void main(String[] args){
    Level level=new Level();
    Minecraft.getInstance().level=level;
    Set<Long> sources=ConcurrentHashMap.newKeySet();
    Set<Long> stable=new HashSet<>();
    for(long i=1;i<=499;i++){sources.add(i);stable.add(i);}
    for(int i=0;i<42;i++)scan(sources,level);
    everyLongLivedSourceVisited(stable,level);
    require(level.inspected.get()==504,
      "Unexpected volume from 12-key source quota "+level.inspected.get());

    // Rebuild the world to start a new full scan, then continuously add
    // and remove 37 unrelated temporary C&B entries while permanent ones
    // remain loaded in the concurrent source map. 90*12 is enough for
    // several scans of the unchanging source population.
    Level churnLevel=new Level();
    Minecraft.getInstance().level=churnLevel;
    sources.clear();
    stable.clear();
    for(long i=100;i<260;i++){sources.add(i);stable.add(i);}
    for(int round=0;round<90;round++){
      for(long n=0;n<37;n++)sources.remove(10000+n+(round-1)*37L);
      for(long n=0;n<37;n++)sources.add(10000+n+round*37L);
      scan(sources,churnLevel);
    }
    everyLongLivedSourceVisited(stable,churnLevel);
    require(churnLevel.inspected.get()<=90*12,
      "Concurrent add/remove triggered an unbounded full C&B map walk");

    // If every source is removed, do not retain a stale iterator that
    // would skip newly placed C&B blocks at the same packed coordinates.
    sources.clear();
    scan(sources,churnLevel);
    require(candidateCursor==null,"Empty source cache retained stale cursor");
    sources.add(42L);
    int before=churnLevel.visits.getOrDefault(42L,new AtomicInteger()).get();
    scan(sources,churnLevel);
    require(churnLevel.visits.get(42L).get()==before+1,
      "C&B source reinstallation was starved after source cache empty");

    // The actual RGB disconnect call must invoke reset() (checked against
    // production above); the production reset must drop all old state.
    reset();
    require(lastLevel==null && candidateCursor==null && ticks==0
            && MISSING.isEmpty() && REPAIRED.isEmpty()
            && REPAIR_ATTEMPTS.isEmpty() && OBSERVED_TILES.isEmpty(),
      "Disconnect retained a Level, stale tile, or 30-second retry quota");

    System.out.println("RGB_PORT_CNB_ROLLING_SOURCE_SCAN_JAVAC_PASS"+
      " stable_499_visited=true concurrent_churn_90_rounds=true"+
      " quota_12_per_40ticks=true empty_to_new_cache=true"+
      " disconnect_level_reference_released=true");
  }
}
'''.replace("/* INJECT_ACTUAL_PRODUCTION_METHODS */",real)

with tempfile.TemporaryDirectory(prefix="rgb-cnb-source-scan-") as td:
    td=Path(td)
    javafile=td/"CnbMeshSourceScanChurnRegression.java"
    javafile.write_text(java,encoding="utf-8")
    for version in ("17","21"):
        classes=td/version
        classes.mkdir()
        c=subprocess.run([
            "javac","--release",version,"-encoding","UTF-8",
            "-d",str(classes),str(javafile)
        ],capture_output=True,text=True,timeout=50)
        if c.returncode:
            raise RuntimeError("Production C&B source scan Java "+version+
              " failed compilation:\n"+c.stdout[-5000:]+c.stderr[-8000:])
        run=subprocess.run([
            "java","-cp",str(classes),
            "com.rgbblocks.client.cnb.CnbMeshSourceScanChurnRegression"
        ],capture_output=True,text=True,timeout=35)
        if run.returncode:
            raise RuntimeError("Production C&B source scan Java "+version+
              " failed:\n"+run.stdout[-5000:]+run.stderr[-8000:])
        assert "RGB_PORT_CNB_ROLLING_SOURCE_SCAN_JAVAC_PASS" in run.stdout
        print("JAVA "+version+" "+run.stdout.strip(),flush=True)
