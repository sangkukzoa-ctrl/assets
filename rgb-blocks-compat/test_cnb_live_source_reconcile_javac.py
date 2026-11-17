#!/usr/bin/env python3
"""Execute the REAL production AUTO RGB/C&B reconciliation on both Java targets.

Extract the exact bounded production methods and stale-packet guard from
RGBRealLightEngine.java. Simulate the saved Forge chaos BLUE -> GREEN 4095-bit
ABA race: C&B tile and rendered geometry are GREEN but live RGB cache remains
BLUE. Also prove MANUAL never publishes a source without the owner's Bake and
that deleted tiles become ghost-light cleanup candidates.

No original owner JAR, Modrinth network access or runtime Mixin changes.
This is a Java logic regression, not a claim about Minecraft graphics.
"""
from pathlib import Path
import subprocess, tempfile

SOURCE=Path("rgb-blocks-compat/recovered/fabric/com/rgbblocks/client/lighting/RGBRealLightEngine.java")
code=SOURCE.read_text(encoding="utf-8")

def extract(signature):
    pos=code.find(signature)
    if pos<0:raise AssertionError("Production RGB method not found: "+signature)
    opening=code.find("{",pos)
    depth=0
    for end in range(opening,len(code)):
        if code[end]=="{":depth+=1
        elif code[end]=="}":
            depth-=1
            if depth==0:return code[pos:end+1]
    raise AssertionError("Unbalanced production method: "+signature)

reconcile=extract("private static void reconcileLoadedCnbSources()")
schedule=extract("private static void scheduleCnbBlockEntity(Object blockEntity, int delayTicks, int attemptsLeft)")
guard_start=code.find("Object currentEntity = isPositionLoaded(pending.pos)")
guard_end=code.find("RGBRealLightEngine.CnbSource previous = sourceFrom(cache, pending.pos)",guard_start)
assert guard_start>=0 and guard_end>guard_start
stale_tile_guard=code[guard_start:guard_end]
removed_start=code.find("long key = cnbKey(pending.pos);\n                  // A queued old C&B update")
removed_end=code.find("// A fast AIR -> C&B replacement",removed_start)
assert removed_start>=0 and removed_end>removed_start
removed_tile_guard=code[removed_start:removed_end]
assert "executeRealCnbRemoval(pending.pos, true)" in removed_tile_guard
assert "deferShadowRemoval(pending.pos)" in removed_tile_guard
assert "currentEntity != pending.blockEntity" in stale_tile_guard
assert "entry.setValue" in stale_tile_guard
assert "continue;" in stale_tile_guard
assert "EFFECTIVE_MODE != RGBRealLightEngine.EffectiveMode.AUTO" in reconcile
assert "RGBRuntime.clientTargetAuto()" in reconcile
assert "ST ALE_CNB_CLEANUP" not in reconcile
for lifecycle in ("static void prepareForPersistenceDimensionSwitch()",
                  "static void restorePersistedCnbSources("):
    body=extract(lifecycle)
    assert "CNB_RECONCILE_CURSOR = null;" in body, (
        "Previous dimension's C&B source cursor survived "+lifecycle)
    assert "CNB_RECONCILE_TICKS = 0;" in body

java=r'''import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
public final class RGBRealLightEngine {
 static final int CNB_RECONCILE_INTERVAL_TICKS=20;
 static final int CNB_RECONCILE_POSITIONS_PER_PASS=32;
 static final int CNB_REFRESH_ATTEMPTS=16;
 static int CNB_RECONCILE_TICKS;
 static Iterator<Long> CNB_RECONCILE_CURSOR;
 static Map<Long,CnbSource> CNB_CACHE=new ConcurrentHashMap<>();
 static Map<Long,PendingCnbRefresh> CNB_PENDING=new ConcurrentHashMap<>();
 static Set<Long> STALE_CNB_CLEANUP=ConcurrentHashMap.newKeySet();
 static Set<Long> DEFERRED_MANUAL_REMOVALS=ConcurrentHashMap.newKeySet();
 static ArrayDeque<Object> ACTIVE_BATCH=new ArrayDeque<>();
 static Map<Long,Tile> WORLD=new HashMap<>();
 static enum EffectiveMode {AUTO, MANUAL_IDLE, MANUAL_BAKING, CATCHING_UP}
 static EffectiveMode EFFECTIVE_MODE=EffectiveMode.AUTO;
 static class RGBRuntime {
   static boolean auto=true;
   static boolean clientTargetAuto(){return auto;}
 }
 static class RGBClientConfig {
   static boolean ENABLE_CNB_SOURCE_TRACKING_CACHED=true;
 }
 static class BlockPos {
   final long k;
   BlockPos(long k){this.k=k;}
   static BlockPos of(long k){return new BlockPos(k);}
   long asLong(){return k;}
   public String toString(){return "C&B@"+k;}
 }
 static class Tile {
   final BlockPos pos;
   final CnbSource live;
   boolean chiseled=true;
   Tile(long key,CnbSource live){this.pos=new BlockPos(key);this.live=live;}
 }
 static class CnbSource {
   final int rgb;
   final float energy;
   CnbSource(int rgb,float energy){this.rgb=rgb;this.energy=energy;}
   boolean active(){return energy>0;}
 }
 static class PendingCnbRefresh {
   final BlockPos pos;
   final Object blockEntity;
   final int delayTicks;
   final int attemptsLeft;
   PendingCnbRefresh(BlockPos pos,Object tile,int delay,int retries){
     this.pos=pos;this.blockEntity=tile;delayTicks=delay;attemptsLeft=retries;
   }
 }
 static boolean enabled(){return true;}
 static BlockPos cnbBlockEntityPos(Object tile){return ((Tile)tile).pos;}
 static long cnbKey(BlockPos pos){return pos.asLong();}
 static boolean isPositionLoaded(BlockPos pos){return WORLD.containsKey(pos.asLong());}
 static boolean isStillChiseledBlock(BlockPos pos){
   Tile tile=WORLD.get(pos.asLong());return tile!=null&&tile.chiseled;
 }
 static Object currentBlockEntity(BlockPos pos){return WORLD.get(pos.asLong());}
 static CnbSource computeCnbSourceFromAccessor(Object tile){return ((Tile)tile).live;}
 static void deferShadowRemoval(BlockPos pos){DEFERRED_MANUAL_REMOVALS.add(pos.asLong());}
 static void executeRealCnbRemoval(BlockPos pos,boolean flag){
   CNB_CACHE.remove(pos.asLong());
 }
 static void markClean(BlockPos pos){}
 /* REAL_RECONCILE_METHOD */
 /* REAL_SCHEDULE_METHOD */
 static void flushPendingOnce(){
   Iterator<Map.Entry<Long,PendingCnbRefresh>> iterator=CNB_PENDING.entrySet().iterator();
   while(iterator.hasNext()){
     Map.Entry<Long,PendingCnbRefresh> entry=iterator.next();
     PendingCnbRefresh pending=entry.getValue();
     boolean shadow=EFFECTIVE_MODE==EffectiveMode.MANUAL_IDLE ||
                    EFFECTIVE_MODE==EffectiveMode.MANUAL_BAKING;
     /* REAL_REMOVED_TILE_GUARD */
     /* REAL_STALE_TILE_GUARD */
     CnbSource actual=computeCnbSourceFromAccessor(pending.blockEntity);
     CNB_CACHE.put(entry.getKey(),actual);
     iterator.remove();
   }
 }
 static void reset(){
   CNB_CACHE.clear();CNB_PENDING.clear();STALE_CNB_CLEANUP.clear();
   DEFERRED_MANUAL_REMOVALS.clear();WORLD.clear();
   ACTIVE_BATCH.clear();CNB_RECONCILE_CURSOR=null;CNB_RECONCILE_TICKS=0;
   EFFECTIVE_MODE=EffectiveMode.AUTO;RGBRuntime.auto=true;
 }
 static void tick(int times){
   for(int i=0;i<times;i++)reconcileLoadedCnbSources();
 }
 static void require(boolean ok,String reason){if(!ok)throw new AssertionError(reason);}
 public static void main(String[]args){
   final long key=73821L;
   CnbSource blue=new CnbSource(0x0855d1,1.0f);
   CnbSource green=new CnbSource(0x3bd119,1.0f);
   CnbSource red=new CnbSource(0xba4860,1.0f);
   // ACTUAL Forge chaos failure: real GREEN tile and 12 model quads, but
   // BLUE cached RGB and adjacent light remain stuck on TWO real clients.
   WORLD.put(key,new Tile(key,green));CNB_CACHE.put(key,blue);
   tick(19);
   require(CNB_PENDING.isEmpty(),"AUTO source reconciling before budgeted interval");
   tick(1);
   require(CNB_PENDING.size()==1,"AUTO never noticed BLUE source vs GREEN C&B tile");
   require(CNB_PENDING.get(key).blockEntity==WORLD.get(key),
           "AUTO must schedule CURRENT GREEN tile, not stale BLUE entity");
   flushPendingOnce();
   require(CNB_CACHE.get(key).rgb==green.rgb,"Source still BLUE after real green relight");
   require(CNB_PENDING.isEmpty(),"Pending source not consumed");
   tick(20);
   require(CNB_PENDING.isEmpty(),"Stable GREEN source should not repeatedly relight");

   // The original 1.3.1 MANUAL user-edited sculpture freezes RGB until Bake.
   reset();WORLD.put(key,new Tile(key,green));CNB_CACHE.put(key,blue);
   RGBRuntime.auto=false;EFFECTIVE_MODE=EffectiveMode.MANUAL_IDLE;
   tick(120);
   require(CNB_PENDING.isEmpty() && CNB_CACHE.get(key).rgb==blue.rgb,
           "MANUAL should preserve BLUE until explicit Bake");
   RGBRuntime.auto=true;
   tick(40);
   require(CNB_PENDING.isEmpty(),"MANUAL idle ignored frozen snapshot");
   EFFECTIVE_MODE=EffectiveMode.CATCHING_UP;
   tick(40);
   require(CNB_PENDING.isEmpty(),"CATCHING_UP should not race fixed dirty batch");
   EFFECTIVE_MODE=EffectiveMode.AUTO;
   tick(20);
   require(CNB_PENDING.size()==1,"AUTO restoration never caught up GREEN tile");

   // Race: queued old BLUE tile, replaced by new GREEN tile at same position.
   reset();
   Tile old=new Tile(key,blue);
   Tile replacement=new Tile(key,green);
   WORLD.put(key,replacement);CNB_CACHE.put(key,blue);
   CNB_PENDING.put(key,new PendingCnbRefresh(new BlockPos(key),old,0,16));
   flushPendingOnce();
   require(CNB_PENDING.containsKey(key),"Old pending packet must retarget live tile");
   require(CNB_PENDING.get(key).blockEntity==replacement,
           "Old BLUE tile still in pending slot");
   require(CNB_CACHE.get(key).rgb==blue.rgb,
           "Retarget must not commit old tile before live reinspection");
   flushPendingOnce();
   require(CNB_CACHE.get(key).rgb==green.rgb,
           "Newly sculpted GREEN tile never superseded old BLUE packet");

   // Negative source: deleted microvoxel blocks must become ghost cleanup.
   reset();Tile deleted=new Tile(key,red);deleted.chiseled=false;
   WORLD.put(key,deleted);CNB_CACHE.put(key,red);
   tick(20);
   require(STALE_CNB_CLEANUP.contains(key),
           "AUTO deleted C&B sculpture did not trigger ghost-source cleanup");
   reset();WORLD.put(key,deleted);CNB_CACHE.put(key,red);
   EFFECTIVE_MODE=EffectiveMode.MANUAL_IDLE;RGBRuntime.auto=false;
   tick(30);
   require(STALE_CNB_CLEANUP.isEmpty(),
           "MANUAL should defer cleanup to user Bake");

   // Pending work should not be repeatedly overwritten by background checks.
   reset();WORLD.put(key,new Tile(key,green));CNB_CACHE.put(key,blue);
   CNB_PENDING.put(key,new PendingCnbRefresh(new BlockPos(key),WORLD.get(key),5,16));
   tick(20);
   require(CNB_PENDING.get(key).delayTicks==5,
           "Reconcile overwrote a legitimate in-flight C&B source request");

   // The real pending-packet implementation must NOT resurrect an RGB
   // emitter when its C&B tile has been deleted and the loaded block is AIR.
   reset();Tile gone=new Tile(key,red);gone.chiseled=false;
   WORLD.put(key,gone);CNB_CACHE.put(key,red);
   CNB_PENDING.put(key,new PendingCnbRefresh(new BlockPos(key),gone,0,16));
   flushPendingOnce();
   require(!CNB_CACHE.containsKey(key) && !CNB_PENDING.containsKey(key),
           "Deleted C&B still has cached RGB light after stale pending packet");
   reset();gone=new Tile(key,red);gone.chiseled=false;
   WORLD.put(key,gone);CNB_CACHE.put(key,red);
   EFFECTIVE_MODE=EffectiveMode.MANUAL_IDLE;RGBRuntime.auto=false;
   CNB_PENDING.put(key,new PendingCnbRefresh(new BlockPos(key),gone,0,16));
   flushPendingOnce();
   require(CNB_CACHE.containsKey(key)&&DEFERRED_MANUAL_REMOVALS.contains(key),
           "MANUAL stale-air removal must be deferred, not published before Bake");

   System.out.println("RGB_PORT_CNB_RGB_AUTO_RECONCILE_REAL_JAVAC_PASS"+
      " blue_to_green=true manual_frozen=true catching_up_safe=true"+
      " old_tile_aba_retargeted=true ghost_air_cleanup=true"+
      " in_flight_request_preserved=true stale_air_packet_rejected=true");
 }
}'''
java=java.replace("/* REAL_RECONCILE_METHOD */",reconcile).replace(
    "/* REAL_SCHEDULE_METHOD */",schedule).replace(
    "/* REAL_REMOVED_TILE_GUARD */",removed_tile_guard).replace(
    "/* REAL_STALE_TILE_GUARD */",stale_tile_guard)

with tempfile.TemporaryDirectory(prefix="rgb-live-reconcile-") as tmp:
    root=Path(tmp)
    target=root/"RGBRealLightEngine.java"
    target.write_text(java,encoding="utf-8")
    for version in ("17","21"):
        destination=root/version
        destination.mkdir()
        build=subprocess.run(["javac","--release",version,"-encoding","UTF-8",
                              "-d",str(destination),str(target)],
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=45)
        if build.returncode:
            raise RuntimeError("REAL C&B RGB source code Java "+version+
                               " compile failed:\n"+build.stdout[-6500:])
        run=subprocess.run(["java","-cp",str(destination),"RGBRealLightEngine"],
               stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30)
        if run.returncode:
            raise RuntimeError("REAL source reconcile logic Java "+version+
                               " failed:\n"+run.stdout[-6500:])
        assert "RGB_PORT_CNB_RGB_AUTO_RECONCILE_REAL_JAVAC_PASS" in run.stdout
        print("JAVA "+version+" "+run.stdout.strip(),flush=True)
