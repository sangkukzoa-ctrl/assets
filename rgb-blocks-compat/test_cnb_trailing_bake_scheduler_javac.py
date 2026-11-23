#!/usr/bin/env python3
"""Execute production C&B trailing debounce, real ScheduledThreadPoolExecutor.

No RGB original author archive or Minecraft client required. Extract exactly
the production Java scheduler, debounce, cancellation and epoch/ABA methods,
compile them with minimal Minecraft stand-ins on Java17 and Java21, and run
actual wall-clock scheduled stress. This is NOT a native Minecraft game PASS.
"""
from pathlib import Path
import subprocess
import tempfile

path=Path("rgb-blocks-compat/recovered/fabric/com/rgbblocks/client/cnb/RGBCnbGeometryBakeDebouncer.java")
production=path.read_text(encoding="utf-8")

def extract(signature):
    begin=production.find(signature)
    assert begin>=0,("Missing production C&B method",signature)
    opening=production.index("{",begin)
    depth=0
    for i in range(opening,len(production)):
        if production[i]=="{":depth+=1
        elif production[i]=="}":
            depth-=1
            if depth==0:return production[begin:i+1]
    raise AssertionError("Unbalanced Java source "+signature)

names=(
    "private static ScheduledThreadPoolExecutor createTrailingScheduler()",
    "public static void reset()",
    "private static void cancelTrailingBake(Entry entry)",
    "private static Entry observeLiveTile(Entry entry, Object tileEntity)",
    "private static void pruneIdleEntries(long now)",
    "public static void runUndebounced(Runnable action)",
    "public static void markPayloadModelUpdate(Object tileEntity)",
    "public static boolean shouldDelayModelBake(Object tileEntity, boolean force)",
    "private static void scheduleTrailingBake(Object tileEntity, BlockPos pos, Entry entry, long serial)",
    "private static Method findModelUpdateMethod(Class<?> entityType)",
    "private static boolean isReplacedClientTile(Object tileEntity, BlockPos pos)",
    "private static boolean isRemoteClientWorld(Object tileEntity)",
    "private static BlockPos getBlockPos(Object tileEntity)",
    "private static long key(BlockPos pos)",
    "private static final class Entry {",
)
real_methods="\n".join(extract(sig) for sig in names)
for required in (
    "setRemoveOnCancelPolicy(true)",
    "entry.pendingFuture.cancel(false)",
    "entry.pendingFuture = TRAILING_BAKES.schedule(",
    "WORLD_EPOCH.incrementAndGet()",
    "cancelTrailingBake(entry)",
    "epoch != WORLD_EPOCH.get()",
    "entry.requestSerial.get() != serial",
    "level.getBlockEntity(pos) != live",
    "isReplacedClientTile(tileEntity, pos)",
    "entry.ownerTile = new WeakReference<>(tileEntity)",
    "entry.lastRequestMillis = 0L",
    "ENTRIES.computeIfPresent(candidate.getKey(), (ignored, current) -> {",
    "entry.requestSerial.incrementAndGet()",
    "update.invoke(live)",
):
    assert required in real_methods,("Real production scheduler safeguard absent",required)
assert ("private static final ScheduledThreadPoolExecutor TRAILING_BAKES = createTrailingScheduler();"
        in production)
# Proof obligation: ConcurrentHashMap.compute() calls observeLiveTile while
# holding its bin lock. Pruning MUST acquire that bin lock before Entry's
# monitor, never Entry -> ENTRIES.remove (AB/BA deadlock).
prune=extract("private static void pruneIdleEntries(long now)")
observe=extract("private static Entry observeLiveTile(Entry entry, Object tileEntity)")
assert "ENTRIES.computeIfPresent(candidate.getKey()" in prune
assert "ENTRIES.remove(" not in prune
assert prune.index("ENTRIES.computeIfPresent(candidate.getKey()") < prune.index("synchronized (current)")
assert "synchronized (entry)" in observe


java=r'''import java.lang.ref.WeakReference;
import java.lang.reflect.Method;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicInteger;

public final class RGBCnbGeometryBakeDebouncer {
   private static final long RAPID_WINDOW_MS=70L;
   private static final long MAX_SUPPRESS_MS=90L;
   private static final long PAYLOAD_ACTIVE_WINDOW_MS=350L;
   private static final int PRUNE_THRESHOLD=4096;
   private static final long ENTRY_IDLE_MS=300000L;
   private static final long PRUNE_INTERVAL_MS=5000L;
   private static final AtomicLong LAST_PRUNE_MS=new AtomicLong();
   private static final Map<Long,Entry> ENTRIES=new ConcurrentHashMap<>();
   private static final ThreadLocal<Boolean> BYPASS=ThreadLocal.withInitial(()->Boolean.FALSE);
   private static final AtomicLong WORLD_EPOCH=new AtomicLong();
   private static final ScheduledThreadPoolExecutor TRAILING_BAKES=createTrailingScheduler();

   static final class BlockPos {
      final int x,y,z;
      BlockPos(int x,int y,int z){this.x=x;this.y=y;this.z=z;}
      BlockPos immutable(){return this;}
      int getX(){return x;}
      int getY(){return y;}
      int getZ(){return z;}
   }
   static class BlockEntity {
      final BlockPos pos;
      final Level level;
      boolean removed;
      final AtomicInteger refreshes=new AtomicInteger();
      BlockEntity(Level level,BlockPos pos){this.level=level;this.pos=pos;}
      public void updateModelData(){refreshes.incrementAndGet();}
      Level getLevel(){return level;}
      BlockPos getBlockPos(){return pos;}
      boolean isRemoved(){return removed;}
   }
   static class Level {
      final Map<Long,BlockEntity> tiles=new HashMap<>();
      final AtomicInteger notifications=new AtomicInteger();
      boolean isClientSide(){return true;}
      boolean isLoaded(BlockPos pos){return tiles.containsKey(key(pos));}
      BlockEntity getBlockEntity(BlockPos pos){return tiles.get(key(pos));}
      Object getBlockState(BlockPos pos){return "chiselsandbits:chiseled";}
      void sendBlockUpdated(BlockPos pos,Object before,Object after,int flag){
        if(flag!=3)throw new AssertionError("Wrong native model-packet flags "+flag);
        notifications.incrementAndGet();
      }
      BlockEntity tile(BlockPos pos){
        BlockEntity b=new BlockEntity(this,pos);
        tiles.put(key(pos),b);
        return b;
      }
   }
   static class Minecraft {
      static final Minecraft INSTANCE=new Minecraft();
      volatile Level level;
      static Minecraft getInstance(){return INSTANCE;}
      void execute(Runnable task){task.run();}
   }

   /* PRODUCTION_METHODS */

   static void require(boolean good,String message){
      if(!good)throw new AssertionError(message);
   }
   static int burst(BlockEntity tile,int count){
      markPayloadModelUpdate(tile);
      int blocked=0;
      for(int i=0;i<count;i++){
         if(shouldDelayModelBake(tile,false))blocked++;
      }
      require(blocked>0,"Test did not generate real suppressed model requests");
      return blocked;
   }
   static void settle()throws Exception{Thread.sleep(330);}
   static void newWorld(Level world){reset();Minecraft.getInstance().level=world;}
   static void verifyNoQueue(){
      require(TRAILING_BAKES.getQueue().isEmpty(),
        "Superseded C&B mesh futures retained in scheduler after reset");
   }
   public static void main(String[] args)throws Exception {
      Level world=new Level();newWorld(world);
      BlockPos one=new BlockPos(10,67,10);
      BlockEntity a=world.tile(one);

      // Several hundred rapid requests on one real entity must schedule
      // AT MOST ONE pending model future, not hundreds of dead futures.
      burst(a,850);
      require(TRAILING_BAKES.getRemoveOnCancelPolicy(),
        "Cancelled scheduled C&B work is retained in the real executor queue");
      require(TRAILING_BAKES.getQueue().size()<=1,
        "Rapid /rgb Bake queued more than one trailing model task");
      settle();
      require(a.refreshes.get()==1 && world.notifications.get()==1,
        "Last C&B model payload was not rebuilt EXACTLY once");
      verifyNoQueue();

      // An explicit force=true rebuild supersedes the old trailing future.
      // The Minecraft/C&B caller performs the actual immediate update
      // whenever shouldDelayModelBake() returns false.
      newWorld(new Level());
      Level forceWorld=Minecraft.getInstance().level;
      BlockEntity forced=forceWorld.tile(new BlockPos(12,67,12));
      burst(forced,500);
      require(TRAILING_BAKES.getQueue().size()<=1,
        "The forced test setup was not properly coalesced");
      require(!shouldDelayModelBake(forced,true),
        "Native force=true model update was unexpectedly blocked");
      forced.updateModelData(); // the immediate model action in the caller
      verifyNoQueue();
      settle();
      require(forced.refreshes.get()==1 && forceWorld.notifications.get()==0,
        "Cancelled older trailing task duplicated the forced model refresh");

      // runUndebounced() is used by the RGB integrity repair callback;
      // it too must supersede any pending 180ms future, even when the
      // underlying native callback calls shouldDelayModelBake(..., false).
      newWorld(new Level());
      Level bypassWorld=Minecraft.getInstance().level;
      BlockEntity bypassed=bypassWorld.tile(new BlockPos(13,67,13));
      burst(bypassed,500);
      runUndebounced(()->{
        require(!shouldDelayModelBake(bypassed,false),
          "RGB integrity repair was unexpectedly debounced");
        bypassed.updateModelData();
      });
      verifyNoQueue();
      settle();
      require(bypassed.refreshes.get()==1 && bypassWorld.notifications.get()==0,
        "Older trailing callback fired after integrity forced repair");

      // A new C&B tile at the same packed coordinate MUST NOT inherit the
      // previous physical tile's 70ms/90ms debounce and 350ms payload clock.
      // The first native model rebuild must execute immediately instead of
      // being silently postponed while Scena starts an obsolete bake.
      newWorld(new Level());
      Level ownerWorld=Minecraft.getInstance().level;
      BlockPos ownerPos=new BlockPos(17,67,17);
      BlockEntity firstOwner=ownerWorld.tile(ownerPos);
      burst(firstOwner,320);
      Entry sharedEntry=ENTRIES.get(key(ownerPos));
      require(sharedEntry.pendingFuture!=null,
        "Old tile must have a pending trailing bake before replacement");
      sharedEntry.lastRequestMillis=System.currentTimeMillis();
      sharedEntry.lastAllowedBakeMillis=sharedEntry.lastRequestMillis;
      BlockEntity freshOwner=ownerWorld.tile(ownerPos);
      markPayloadModelUpdate(freshOwner);
      require(sharedEntry.ownerTile.get()==freshOwner,
        "Tile replacement did not bind the debounce entry to new C&B entity");
      require(sharedEntry.lastRequestMillis==0L &&
              sharedEntry.lastAllowedBakeMillis==0L,
        "New C&B entity inherited the old tile's rapid-bake timestamps");
      require(sharedEntry.requestSerial.get()>0L &&
              sharedEntry.pendingFuture==null,
        "New C&B owner did not invalidate old tile pending mesh work");
      require(!shouldDelayModelBake(freshOwner,false),
        "New tile's FIRST authoritative C&B Bake was incorrectly delayed");
      require(sharedEntry.lastRequestMillis>0L &&
              sharedEntry.ownerTile.get()==freshOwner,
        "First new-tile request was not recorded for current owner");
      // Follow-up requests are once again coalesced for the NEW owner.
      burst(freshOwner,240);
      settle();
      require(firstOwner.refreshes.get()==0 &&
              freshOwner.refreshes.get()==1,
        "Old C&B tile's pending Bake survived ownership change");
      verifyNoQueue();

      // ABA before the timer runs: a REMOVED prior C&B entity must not
      // mutate the pending entry for the new installed tile. The old
      // implementation only checked live tile identity at EXECUTION time,
      // so a stale FORCE, bypass or normal event first CANCELLED the newer
      // tile's only trailing future and the stale task later did nothing.
      newWorld(new Level());
      Level staleWorld=Minecraft.getInstance().level;
      BlockPos shared=new BlockPos(14,67,14);
      BlockEntity obsolete=staleWorld.tile(shared);
      BlockEntity current=staleWorld.tile(shared);
      burst(current,490);
      Entry pending=ENTRIES.get(key(shared));
      ScheduledFuture<?> goodFuture=pending.pendingFuture;
      long goodSerial=pending.requestSerial.get();
      pending.lastPayloadMillis=19L; // detect stale payload mutation exactly
      markPayloadModelUpdate(obsolete);
      require(pending.lastPayloadMillis==19L,
        "Obsolete payload overwrote current C&B tile's debounce epoch");
      require(!shouldDelayModelBake(obsolete,false),
        "Obsolete normal C&B tile should not be postponed");
      require(!shouldDelayModelBake(obsolete,true),
        "Obsolete forced C&B tile should not be postponed");
      runUndebounced(()->require(!shouldDelayModelBake(obsolete,false),
        "Obsolete bypass C&B tile should not be postponed"));
      require(pending.requestSerial.get()==goodSerial,
        "Obsolete tile unexpectedly invalidated replacement model serial");
      require(pending.pendingFuture==goodFuture && !goodFuture.isCancelled(),
        "Obsolete tile cancelled the replacement's only scheduled mesh bake");
      settle();
      require(current.refreshes.get()==1 && obsolete.refreshes.get()==0,
        "Stale C&B ABA callback stole the new tile's final mesh publication");
      verifyNoQueue();

      // Also reject an entity marked removed before it is detached from
      // the client level map (short-lived normal teardown ordering).
      newWorld(new Level());
      Level removalWorld=Minecraft.getInstance().level;
      BlockEntity removed=removalWorld.tile(new BlockPos(18,67,18));
      burst(removed,420);
      Entry prior=ENTRIES.get(key(removed.getBlockPos()));
      long beforeRemoved=prior.requestSerial.get();
      removed.removed=true;
      markPayloadModelUpdate(removed);
      require(!shouldDelayModelBake(removed,true),
        "Removed tile force request should be ignored");
      require(prior.requestSerial.get()==beforeRemoved &&
              prior.pendingFuture!=null && !prior.pendingFuture.isCancelled(),
        "Removed tile invalidated a still-tracked C&B job");
      reset();
      verifyNoQueue();

      // Two independent C&B positions each keep their own single future.
      newWorld(new Level());
      Level twoWorld=Minecraft.getInstance().level;
      BlockEntity left=twoWorld.tile(new BlockPos(15,67,15));
      BlockEntity right=twoWorld.tile(new BlockPos(16,67,15));
      burst(left,320);
      burst(right,320);
      require(TRAILING_BAKES.getQueue().size()<=2,
        "Two C&B sources have unbounded queued trailing bakes");
      settle();
      require(left.refreshes.get()==1 && right.refreshes.get()==1,
        "Two independent C&B sources suppressed each other");

      // Disconnect must cancel all scheduled jobs immediately, not merely
      // wait 180ms for epoch-rejected scheduled closures to be invoked.
      newWorld(new Level());
      Level abortWorld=Minecraft.getInstance().level;
      BlockEntity abort=abortWorld.tile(new BlockPos(30,67,30));
      burst(abort,550);
      reset();
      verifyNoQueue();
      settle();
      require(abort.refreshes.get()==0 && abortWorld.notifications.get()==0,
        "Disconnected C&B world was asynchronously rebuilt");
      Minecraft.getInstance().level=null;

      // ABA: old C&B block disappears and new C&B tile takes same position.
      newWorld(new Level());
      Level abaWorld=Minecraft.getInstance().level;
      BlockPos abaPos=new BlockPos(40,67,40);
      BlockEntity stale=abaWorld.tile(abaPos);
      burst(stale,370);
      stale.removed=true;
      BlockEntity replacement=abaWorld.tile(abaPos);
      burst(replacement,370);
      require(TRAILING_BAKES.getQueue().size()<=1,
        "ABA replacement left an older tile future in the queue");
      settle();
      require(stale.refreshes.get()==0 && replacement.refreshes.get()==1,
        "Stale C&B tile rebuilt the replacement's model data");

      // A world identity change without explicit reset must still be
      // rejected by the existing world identity guard.
      newWorld(new Level());
      Level oldWorld=Minecraft.getInstance().level;
      BlockEntity old=oldWorld.tile(new BlockPos(50,67,50));
      burst(old,480);
      Minecraft.getInstance().level=new Level();
      settle();
      require(old.refreshes.get()==0,
        "Prior world model callback executed in the new live Minecraft level");

      // Thousands of historical chisels in a single long session should
      // not retain 4k+ idle per-position debouncer records indefinitely.
      // Force a five-minute virtual aging of EXACT Java Entry timestamps;
      // current real pending work must not be evicted by a simultaneous
      // cache sweep, nor can old cancelled callbacks be resurrected.
      newWorld(new Level());
      Level cacheWorld=Minecraft.getInstance().level;
      for(int n=0;n<4230;n++){
         BlockEntity cached=cacheWorld.tile(new BlockPos(n,78,100));
         markPayloadModelUpdate(cached);
      }
      require(ENTRIES.size()==4230,
        "Cache pressure fixture did not create independent C&B positions");
      BlockEntity active=cacheWorld.tile(new BlockPos(6000,78,100));
      burst(active,390);
      Entry activeEntry=ENTRIES.get(key(active.getBlockPos()));
      ScheduledFuture<?> activeFuture=activeEntry.pendingFuture;
      require(activeFuture!=null && !activeFuture.isCancelled(),
        "A new active mesh build was not scheduled");
      for(Entry entry:ENTRIES.values()){
         if(entry!=activeEntry){
            entry.lastTouchedMillis=System.currentTimeMillis()-ENTRY_IDLE_MS-30000L;
         }
      }
      LAST_PRUNE_MS.set(0L); // force an otherwise 5-second-rate-limited sweep
      BlockEntity trigger=cacheWorld.tile(new BlockPos(7000,78,100));
      markPayloadModelUpdate(trigger);
      require(ENTRIES.size()<=3,
        "Idle C&B sources were not pruned after five minutes; count="+ENTRIES.size());
      require(ENTRIES.get(key(active.getBlockPos()))==activeEntry &&
              activeEntry.pendingFuture==activeFuture &&
              !activeFuture.isCancelled(),
        "Idle C&B cleanup cancelled a freshly scheduled ACTIVE mesh job");
      settle();
      require(active.refreshes.get()==1,
        "Recent C&B geometry update was lost during idle map cleanup");
      reset();
      require(ENTRIES.isEmpty() && LAST_PRUNE_MS.get()==0L,
        "Disconnect did not release the entire long-session C&B debounce map");
      verifyNoQueue();

      // Deterministic lock-order contention: this worker holds the CHM
      // packed-position bin lock while a second worker prunes that entry.
      // The old Entry->map.remove path could deadlock the two JVM threads
      // if the producer then tried to enter observeLiveTile(Entry).
      newWorld(new Level());
      Level contentionWorld=Minecraft.getInstance().level;
      BlockPos contestedPos=new BlockPos(0,0,0);
      BlockEntity contested=contentionWorld.tile(contestedPos);
      markPayloadModelUpdate(contested);
      long contestedKey=key(contestedPos);
      Entry original=ENTRIES.get(contestedKey);
      original.lastTouchedMillis=0L;
      for(int n=0;n<4220;n++){
        Entry idle=new Entry();
        idle.lastTouchedMillis=0L;
        ENTRIES.put(key(new BlockPos(50000+n,90,90)),idle);
      }
      require(ENTRIES.size()>PRUNE_THRESHOLD,
        "Lock-order regression missing C&B source map pressure");
      LAST_PRUNE_MS.set(0L);
      CountDownLatch hasBin=new CountDownLatch(1);
      CountDownLatch releaseBin=new CountDownLatch(1);
      ExecutorService contending=Executors.newFixedThreadPool(2);
      Future<?> producer=contending.submit(()->{
        ENTRIES.compute(contestedKey,(key,current)->{
          hasBin.countDown();
          try{
            if(!releaseBin.await(5,TimeUnit.SECONDS))
              throw new AssertionError("Bin-lock handshake stuck");
          }catch(InterruptedException failure){
            Thread.currentThread().interrupt();
            throw new RuntimeException(failure);
          }
          return observeLiveTile(current,contested);
        });
      });
      require(hasBin.await(3,TimeUnit.SECONDS),
        "Concurrent C&B producer did not acquire its map bin lock");
      Future<?> purge=contending.submit(()->pruneIdleEntries(
        System.currentTimeMillis()));
      Thread.sleep(80);
      releaseBin.countDown();
      producer.get(8,TimeUnit.SECONDS);
      purge.get(8,TimeUnit.SECONDS);
      contending.shutdown();
      require(contending.awaitTermination(4,TimeUnit.SECONDS),
        "C&B source lock-order stress left a blocked Java thread");
      require(ENTRIES.get(contestedKey)==original &&
              original.lastTouchedMillis>0L,
        "Prune removed the active C&B tile after concurrent producer touched it");
      reset();
      verifyNoQueue();
      System.out.println("RGB_PORT_CNB_SCHEDULED_COALESCING_REAL_JAVAC_PASS"+
        " burst_850_queue_one=true independent_two_positions=true"+
        " forced_refresh_cancels_stale_future=true"+
        " bypass_refresh_cancels_stale_future=true"+
        " stale_aba_request_cannot_cancel_live=true"+
        " new_tile_first_bake_not_delayed=true"+
        " idle_4230_records_pruned=true"+
        " live_future_survives_idle_prune=true"+
        " concurrent_bin_entry_lock_order=true"+
        " removed_tile_request_ignored=true"+
        " disconnect_cancels_queue=true aba_no_stale_tile=true"+
        " world_guard=true last_model_update_once=true");
      TRAILING_BAKES.shutdownNow();
   }
}
'''.replace("/* PRODUCTION_METHODS */",real_methods)

with tempfile.TemporaryDirectory(prefix="rgb-cnb-scheduled-coalesce-") as td:
    root=Path(td)
    file=root/"RGBCnbGeometryBakeDebouncer.java"
    file.write_text(java,encoding="utf-8")
    for version in ("17","21"):
        target=root/("java"+version)
        target.mkdir()
        build=subprocess.run(
          ["javac","--release",version,"-encoding","UTF-8",
           "-d",str(target),str(file)],
          capture_output=True,text=True,timeout=50)
        if build.returncode:
            raise RuntimeError("C&B production scheduled coalescer Java "+version+
              " compilation error:\n"+build.stdout[-4000:]+build.stderr[-9000:])
        result=subprocess.run(
          ["java","-cp",str(target),"RGBCnbGeometryBakeDebouncer"],
          capture_output=True,text=True,timeout=35)
        if result.returncode:
            raise RuntimeError("C&B production scheduled coalescer Java "+version+
              " regression failed:\n"+result.stdout[-5000:]+result.stderr[-8000:])
        assert "RGB_PORT_CNB_SCHEDULED_COALESCING_REAL_JAVAC_PASS" in result.stdout
        print("JAVA "+version+" "+result.stdout.strip(),flush=True)
