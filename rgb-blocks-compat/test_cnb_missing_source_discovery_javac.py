#!/usr/bin/env python3
"""Offline Java17/21 replay: owner RGB disappears from CACHE on peer rejoin.

Extract and compile the EXACT 1.20.1/1.21.1 production C&B source discovery
methods, not a rewritten algorithm. Simulates both near and distant loaded
chunks, a genuine C&B tile that arrives with 4095 colored microbits but no
RGB cache entry, MANUAL preservation, and old-world cooldown invalidation.

This is a production-logic Java test; not a real Minecraft runtime claim.
"""
from pathlib import Path
import subprocess, tempfile

SOURCE=Path("rgb-blocks-compat/recovered/fabric/com/rgbblocks/client/lighting/RGBRealLightEngine.java")
code=SOURCE.read_text(encoding="utf-8")

def extract(signature):
    start=code.find(signature)
    assert start>=0,("Missing RGB source production method",signature)
    opening=code.find("{",start)
    assert opening>=0
    depth=0
    for cursor in range(opening,len(code)):
        if code[cursor]=="{":
            depth+=1
        elif code[cursor]=="}":
            depth-=1
            if depth==0:
                return code[start:cursor+1]
    raise AssertionError(("Unbalanced production Java method",signature))

parts={
    "/* SOURCE_OFFSETS */":extract("private static List<int[]> buildCnbDiscoveryOffsets()"),
    "/* SOURCE_RESET */":extract("private static void resetCnbDiscovery()"),
    "/* SOURCE_DISCOVERY */":extract("private static void discoverMissingLoadedCnbSources()"),
    "/* SOURCE_SCHEDULER */":extract("private static void scheduleCnbBlockEntity(Object blockEntity, int delayTicks, int attemptsLeft)"),
}
assert "getChunkSource().getChunk(cx + off[0], cz + off[1], false)" in parts["/* SOURCE_DISCOVERY */"]
assert "CNB_CACHE.containsKey(key)" in parts["/* SOURCE_DISCOVERY */"]
assert "CNB_PENDING.containsKey(key)" in parts["/* SOURCE_DISCOVERY */"]
assert "EFFECTIVE_MODE != RGBRealLightEngine.EffectiveMode.AUTO" in parts["/* SOURCE_DISCOVERY */"]
assert "CNB_DISCOVERY_LAST_CHECK.put(key, CNB_DISCOVERY_TICK);" in parts["/* SOURCE_DISCOVERY */"]
for marker in ("public static void invalidateAll()","public static void onClientDisconnect()",
               "static void prepareForPersistenceDimensionSwitch()",
               "static void restorePersistedCnbSources(",
               "private static void finishToAuto()"):
    assert "resetCnbDiscovery();" in extract(marker),("Missing dimension/lifecycle reset",marker)

java=r'''import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
public final class RGBRealLightEngine {
  static final int CNB_DISCOVERY_RADIUS_CHUNKS=16;
  static final int CNB_DISCOVERY_CHUNKS_PER_PASS=16;
  static final int CNB_DISCOVERY_INTERVAL_TICKS=10;
  static final long CNB_DISCOVERY_RETRY_COOLDOWN_TICKS=400L;
  static final int CNB_REFRESH_ATTEMPTS=16;
  static final List<int[]> CNB_DISCOVERY_OFFSETS=buildCnbDiscoveryOffsets();
  static final Map<Long,Long> CNB_DISCOVERY_LAST_CHECK=new ConcurrentHashMap<>();
  static final Map<Long,CnbSource> CNB_CACHE=new ConcurrentHashMap<>();
  static final Map<Long,PendingCnbRefresh> CNB_PENDING=new ConcurrentHashMap<>();
  static final ArrayDeque<Object> ACTIVE_BATCH=new ArrayDeque<>();
  static int CNB_DISCOVERY_CURSOR;
  static long CNB_DISCOVERY_TICK;
  static Object CNB_DISCOVERY_WORLD;
  static enum EffectiveMode {AUTO, MANUAL_IDLE, MANUAL_BAKING,CATCHING_UP}
  static EffectiveMode EFFECTIVE_MODE=EffectiveMode.AUTO;
  static final class RGBRuntime {
    static boolean wantsAuto=true;
    static boolean clientTargetAuto(){return wantsAuto;}
  }
  static final class RGBClientConfig {
    static boolean ENABLE_CNB_SOURCE_TRACKING_CACHED=true;
  }
  static final class BlockPos {
    private final long id;
    BlockPos(long id){this.id=id;}
    long asLong(){return id;}
  }
  static class BlockEntity {
    BlockPos position;
    boolean removed=false;
    BlockEntity(long id){this.position=new BlockPos(id);}
    boolean isRemoved(){return removed;}
    BlockPos getBlockPos(){return position;}
  }
  static final class chiselsandbitsTile extends BlockEntity {
    final CnbSource source;
    boolean chiseled=true;
    chiselsandbitsTile(long id,int rgb){
      super(id);source=new CnbSource(rgb,1.0f);
    }
  }
  static final class unrelatedTile extends BlockEntity {
    unrelatedTile(long id){super(id);}
  }
  static class CnbSource {
    final int rgb;final float energy;
    CnbSource(int rgb,float energy){this.rgb=rgb;this.energy=energy;}
    boolean active(){return energy>0;}
  }
  static final class PendingCnbRefresh {
    final BlockPos pos;final Object blockEntity;
    final int delayTicks;final int attemptsLeft;
    PendingCnbRefresh(BlockPos pos,Object be,int d,int a){
      this.pos=pos;this.blockEntity=be;
      delayTicks=d;attemptsLeft=a;
    }
  }
  static class LevelChunk {
    final Map<BlockPos,BlockEntity> entities=new HashMap<>();
    Map<BlockPos,BlockEntity> getBlockEntities(){return entities;}
    void add(BlockEntity be){entities.put(be.getBlockPos(),be);}
  }
  static class ChunkSource {
    final Map<Long,LevelChunk> chunks=new HashMap<>();
    int lookupCount=0;
    int forcedLoads=0;
    static long key(int x,int z){return ((long)x<<32)^(z&0xffffffffL);}
    LevelChunk getChunk(int x,int z,boolean force){
      lookupCount++;
      if(force)forcedLoads++;
      return chunks.get(key(x,z));
    }
    void set(int x,int z,LevelChunk chunk){chunks.put(key(x,z),chunk);}
  }
  static class ClientLevel {
    final ChunkSource source=new ChunkSource();
    ChunkSource getChunkSource(){return source;}
  }
  static class Player {
    int x,z;
    int getBlockX(){return x;}
    int getBlockZ(){return z;}
  }
  static class Minecraft {
    static final Minecraft INSTANCE=new Minecraft();
    ClientLevel level;
    Player player=new Player();
    static Minecraft getInstance(){return INSTANCE;}
  }
  static final Map<Long,BlockEntity> REAL_TILES=new HashMap<>();
  static boolean enabled(){return true;}
  static long cnbKey(BlockPos pos){return pos.asLong();}
  static BlockPos cnbBlockEntityPos(Object be){return ((BlockEntity)be).getBlockPos();}
  static boolean isStillChiseledBlock(BlockPos pos){
    BlockEntity be=REAL_TILES.get(pos.asLong());
    return be instanceof chiselsandbitsTile && ((chiselsandbitsTile)be).chiseled;
  }
  /* SOURCE_OFFSETS */
  /* SOURCE_RESET */
  /* SOURCE_DISCOVERY */
  /* SOURCE_SCHEDULER */
  static void advance(int ticks){
    for(int t=0;t<ticks;t++)discoverMissingLoadedCnbSources();
  }
  static void check(boolean okay,String message){
    if(!okay)throw new AssertionError(message);
  }
  static void clearTest(){
    resetCnbDiscovery();CNB_CACHE.clear();CNB_PENDING.clear();
    ACTIVE_BATCH.clear();REAL_TILES.clear();
    Minecraft.INSTANCE.level=null;
    Minecraft.INSTANCE.player.x=0;Minecraft.INSTANCE.player.z=0;
    RGBRuntime.wantsAuto=true;EFFECTIVE_MODE=EffectiveMode.AUTO;
  }
  static ClientLevel worldWithChunk(int x,int z,BlockEntity tile){
    ClientLevel world=new ClientLevel();
    LevelChunk chunk=new LevelChunk();chunk.add(tile);
    world.source.set(x,z,chunk);
    REAL_TILES.put(tile.getBlockPos().asLong(),tile);
    return world;
  }
  public static void main(String[] args){
    check(CNB_DISCOVERY_OFFSETS.size()==1089,"Wrong 33x33 chunk discovery radius");
    check(Arrays.equals(CNB_DISCOVERY_OFFSETS.get(0),new int[]{0,0}),
          "First discovery must prioritize the player's current chunk");
    Set<String> unique=new HashSet<>();
    for(int[] off:CNB_DISCOVERY_OFFSETS){
      check(Math.abs(off[0])<=16&&Math.abs(off[1])<=16,"Chunk offset outside radius");
      unique.add(off[0]+":"+off[1]);
    }
    check(unique.size()==1089,"Duplicate/missing chunk offsets");
    long p=8841L;
    // Historical NeoForge post-chaos rejoin: C&B block/4095 voxel contents
    // present, but no CNB_CACHE entry (RGB stays BLACK for 1680 ticks).
    clearTest();
    chiselsandbitsTile tile=new chiselsandbitsTile(p,0x3bd119);
    Minecraft.INSTANCE.level=worldWithChunk(0,0,tile);
    advance(9);
    check(CNB_PENDING.isEmpty(),"Unbounded eager scanning before throttle");
    advance(1);
    check(CNB_PENDING.containsKey(p),"CACHE-MISS never rediscovered current C&B");
    check(CNB_PENDING.get(p).blockEntity==tile,"Wrong tile used for RGB bootstrap");
    check(Minecraft.INSTANCE.level.source.forcedLoads==0,
          "Discovery must NEVER generate/reload unloaded chunks");
    CNB_PENDING.clear();CNB_CACHE.put(p,tile.source);
    advance(20);
    check(CNB_PENDING.isEmpty(),"Already-known source redundantly scanned");

    // Do not overwrite the owner's manually baked/frozen lighting.
    clearTest();
    tile=new chiselsandbitsTile(p,0x3bd119);
    Minecraft.INSTANCE.level=worldWithChunk(0,0,tile);
    RGBRuntime.wantsAuto=false;EFFECTIVE_MODE=EffectiveMode.MANUAL_IDLE;
    advance(150);
    check(CNB_PENDING.isEmpty(),"MANUAL source mutated without Bake");
    RGBRuntime.wantsAuto=true;EFFECTIVE_MODE=EffectiveMode.CATCHING_UP;
    advance(100);
    check(CNB_PENDING.isEmpty(),"CATCHING_UP violated batch determinism");
    EFFECTIVE_MODE=EffectiveMode.AUTO;
    advance(10);
    check(CNB_PENDING.containsKey(p),"AUTO did not discover deferred source");

    // Unrelated block entities must not become phantom C&B light emitters.
    clearTest();
    unrelatedTile unrelated=new unrelatedTile(4321);
    Minecraft.INSTANCE.level=worldWithChunk(0,0,unrelated);
    advance(10);
    check(CNB_PENDING.isEmpty(),"Unrelated entity became RGB light");

    // A C&B tile containing only non-glow materials: schedule at most once
    // per 400 ticks when the loader leaves the RGB cache absent.
    clearTest();
    tile=new chiselsandbitsTile(p,0);
    Minecraft.INSTANCE.level=worldWithChunk(0,0,tile);
    advance(10);
    check(CNB_PENDING.containsKey(p),"Non-emitter not checked for C&B source");
    CNB_PENDING.clear();
    CNB_DISCOVERY_CURSOR=0;
    advance(10);
    check(CNB_PENDING.isEmpty(),"Missing-source check ignored anti-spam cooldown");

    // World swap must recheck same coordinates in another dimension.
    clearTest();
    tile=new chiselsandbitsTile(p,0x0855d1);
    ClientLevel oldWorld=worldWithChunk(0,0,tile);
    Minecraft.INSTANCE.level=oldWorld;
    advance(10);
    check(CNB_DISCOVERY_LAST_CHECK.containsKey(p),"First world source not visited");
    CNB_PENDING.clear();REAL_TILES.clear();
    chiselsandbitsTile newTile=new chiselsandbitsTile(p,0x3bd119);
    Minecraft.INSTANCE.level=worldWithChunk(0,0,newTile);
    advance(10);
    check(CNB_PENDING.containsKey(p),"Different world reused old cooldown");
    check(CNB_PENDING.get(p).blockEntity==newTile,
          "Different dimension source used old block entity");
    check(Minecraft.INSTANCE.level.source.forcedLoads==0,
          "Different world discovery forced a chunk load");

    // Other C&B fixture may be far from peer's post-chaos position, yet
    // still inside loaded view distance. A bounded full ring eventually
    // discovers it without requiring a block-change network packet.
    clearTest();
    tile=new chiselsandbitsTile(p,0x3bd119);
    Minecraft.INSTANCE.player.x=160; // player's chunk = +10, C&B at 0
    Minecraft.INSTANCE.level=worldWithChunk(0,0,tile);
    advance(700);
    check(CNB_PENDING.containsKey(p),
          "Distant loaded GREEN 4095-bit sculpture remains RGB BLACK after reconnect");
    check(Minecraft.INSTANCE.level.source.forcedLoads==0,
          "Distant discovery generated chunks or caused extra world loading");
    check(Minecraft.INSTANCE.level.source.lookupCount<=1120,
          "Repeated scans exceeded 16 loaded-chunk lookups per ten ticks");

    System.out.println("RGB_PORT_CNB_MISSING_SOURCE_REAL_JAVAC_PASS"+
      " reconnect_cache_miss=true far_loaded_tile=true manual_frozen=true"+
      " no_chunk_generation=true world_switch=true cooldown=true"+
      " client_chunk_budget=16_per_10_ticks");
  }
}'''
for marker,body in parts.items():
    assert java.count(marker)==1,marker
    java=java.replace(marker,body)
with tempfile.TemporaryDirectory(prefix="rgb-cnb-source-discovery-") as tmp:
    root=Path(tmp)
    path=root/"RGBRealLightEngine.java"
    path.write_text(java,encoding="utf-8")
    for java_version in ("17","21"):
        out=root/java_version
        out.mkdir()
        build=subprocess.run(["javac","--release",java_version,"-encoding","UTF-8",
                              "-d",str(out),str(path)],capture_output=True,text=True,timeout=45)
        if build.returncode:
            raise RuntimeError("C&B production cache-miss discovery Java "+
                               java_version+" compilation failed:\n"+build.stderr[-7000:])
        run=subprocess.run(["java","-cp",str(out),"RGBRealLightEngine"],
                           capture_output=True,text=True,timeout=25)
        if run.returncode:
            raise RuntimeError("C&B source cache-miss runtime Java "+
                               java_version+" failed:\n"+run.stdout[-4000:]+run.stderr[-4000:])
        assert "RGB_PORT_CNB_MISSING_SOURCE_REAL_JAVAC_PASS" in run.stdout
        print("JAVA "+java_version+" "+run.stdout.strip(),flush=True)
