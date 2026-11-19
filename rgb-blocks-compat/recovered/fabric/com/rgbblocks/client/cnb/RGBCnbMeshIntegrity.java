package com.rgbblocks.client.cnb;

import com.rgbblocks.client.lighting.RGBRenderInvalidator;
import java.lang.reflect.Method;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import net.minecraft.client.Minecraft;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/**
 * C&B's voxel stats and RGB light may remain correct while the independently
 * asynchronous Scena baked model becomes an EMPTY model after repeated /rgb
 * bakes / distant chunk rebuilds. This is a narrowly bounded mesh-only rescue.
 *
 * No reference to a C&B/Scena *class* at linkage time: RGB still runs alone.
 * Never changes bits, NBT, server packets or RGB light caches.
 */
public final class RGBCnbMeshIntegrity {
   private static final Map<Long,Integer> MISSING = new HashMap<>();
   private static final Map<Long,Long> REPAIRED = new HashMap<>();
   // A C&B -> AIR -> stone -> C&B ABA can create a different tile at the
   // SAME packed position while the 30-second repair cooldown is live.
   // Associate the cooldown with the actual current tile, not coordinates.
   // Weak handles do not retain long-unloaded model/level instances.
   private static final Map<Long,WeakReference<BlockEntity>> OBSERVED_TILES = new HashMap<>();
   // Real C&B/Scena API failures must be visible to owner-hostile CI.
   // Log once per source per 30 seconds maximum; never flood player logs.
   private static final Map<Long,Long> LAST_ORACLE_ERROR = new HashMap<>();
   private static Level lastLevel;
   private static long ticks;
   private static int cursor;
   private static final long REPAIR_COOLDOWN_TICKS = 600L;
   private RGBCnbMeshIntegrity(){}

   public static void reset(){
      lastLevel=null;
      MISSING.clear();
      REPAIRED.clear();
      OBSERVED_TILES.clear();
      LAST_ORACLE_ERROR.clear();
      ticks=0L;
      cursor=0;
   }

   public static void check(Set<Long> candidateSources){
      Minecraft client=Minecraft.getInstance();
      if(client==null || client.level==null)return;
      Level level=client.level;
      if(level!=lastLevel){
         reset();
         lastLevel=level;
      }
      // Every TWO seconds, at most 12 C&B RGB sources out of the currently
      // loaded client light cache. Round-robin rather than always choosing
      // the first source, so far sculptures get checked on re-entry.
      if(++ticks%40L!=0L || candidateSources==null || candidateSources.isEmpty())return;
      ArrayList<Long> entries=new ArrayList<>(candidateSources);
      int size=entries.size();
      int toInspect=Math.min(12,size);
      for(int i=0;i<toInspect;i++){
         Long id=entries.get(Math.floorMod(cursor+i,size));
         if(id==null)continue;
         BlockPos pos=BlockPos.of(id.longValue());
         if(!level.isLoaded(pos)){
            MISSING.remove(id);
            REPAIRED.remove(id);
            OBSERVED_TILES.remove(id);
            continue;
         }
         try{
            BlockEntity tile=level.getBlockEntity(pos);
            if(tile==null || tile.isRemoved() ||
              !tile.getClass().getName().contains("chiselsandbits")){
               MISSING.remove(id);
               REPAIRED.remove(id);
               OBSERVED_TILES.remove(id);
               continue;
            }
            String name=String.valueOf(BuiltInRegistries.BLOCK.getKey(
                 level.getBlockState(pos).getBlock()));
            if(!"chiselsandbits:chiseled".equals(name)){
               MISSING.remove(id);
               REPAIRED.remove(id);
               OBSERVED_TILES.remove(id);
               continue;
            }
            WeakReference<BlockEntity> observed=OBSERVED_TILES.get(id);
            if(observed==null || observed.get()!=tile){
               // A new physical tile MUST get its own three-strike grace
               // and recovery opportunity, even inside the old tile's
               // 600-tick cooldown. ABA may occur entirely between scans.
               MISSING.remove(id);
               REPAIRED.remove(id);
               OBSERVED_TILES.put(id,new WeakReference<>(tile));
            }
            if(!hasActualVoxelStates(tile)){
               MISSING.remove(id);
               REPAIRED.remove(id); // AIR-only -> Glow in-place can recover
               continue;
            }
            if(hasActualRenderedQuads(tile)){
               MISSING.remove(id);
               continue;
            }
            int strikes=MISSING.merge(id,1,Integer::sum);
            if(strikes<3)continue; // 6-second grace for normal async mesh load
            long previous=REPAIRED.getOrDefault(id,-REPAIR_COOLDOWN_TICKS);
            if(ticks-previous<REPAIR_COOLDOWN_TICKS)continue;
            // A failed C&B/Scena model callback is NOT a successful
            // repair. Do not poison the next retry with a 600-tick cooldown.
            MISSING.remove(id);
            // Safe on CLIENT game thread, and only for a CURRENT loaded tile.
            // C&B's own async update publishes the model then requests the
            // native chunk renderer to rebuild, preserving RGB baked light.
            RGBCnbGeometryBakeDebouncer.runUndebounced(()->{
               try{
                  Method update=findZeroArg(tile.getClass(),"updateModelData");
                  update.invoke(tile);
                  RGBRenderInvalidator.dirtyAround(pos,2);
                  REPAIRED.put(id,ticks); // consume cooldown only on success
                  System.out.println("[RGB Blocks] Restoring missing C&B mesh quads at "
                     +pos+" without modifying RGB or voxel data");
               }catch(Throwable err){
                  // Existing 600-tick per-position diagnostic throttle;
                  // a transient async model failure retries after 3 strikes.
                  logOracleFailure(id,pos,err);
               }
            });
         }catch(Throwable failure){
            // A hidden reflection error previously disabled this entire
            // repair while 4095 actual C&B bits and RGB light stayed present.
            // Keep RGB standalone-safe, but preserve bounded error evidence.
            logOracleFailure(id,pos,failure);
         }
      }
      cursor=(cursor+toInspect)%size;
      if(MISSING.size()>4096)MISSING.clear();
      if(REPAIRED.size()>4096)REPAIRED.clear();
      if(OBSERVED_TILES.size()>4096)OBSERVED_TILES.clear();
   }

   private static boolean hasActualVoxelStates(BlockEntity tile)throws ReflectiveOperationException{
      Object statistics=findZeroArg(tile.getClass(),"getStatistics").invoke(tile);
      Method method=findZeroArg(statistics.getClass(),"getStateCounts");
      method.setAccessible(true);
      Object counts=method.invoke(statistics);
      if(!(counts instanceof Map<?,?> map))return false;
      // C&B statistics may include AIR -> 4096 while the sculpture has no
      // visible bits. Air is NOT a valid reason to resurrect an empty model.
      // 1.21.1 C&B uses BlockInformation.blockState(), while 1.20.1 uses
      // IBlockInformation.getBlockState(). Check BOTH native APIs.
      for(Map.Entry<?,?> entry:map.entrySet()){
         Object count=entry.getValue();
         if(!(count instanceof Number n) || n.intValue()<=0)continue;
         Object information=entry.getKey();
         if(information==null)continue;
         BlockState state=null;
         if(information instanceof BlockState direct)state=direct;
         else{
            try{
               Object candidate=findZeroArg(information.getClass(),"blockState")
                      .invoke(information);
               if(candidate instanceof BlockState found)state=found;
            }catch(NoSuchMethodException olderApi){
               Object candidate=findZeroArg(information.getClass(),"getBlockState")
                      .invoke(information);
               if(candidate instanceof BlockState found)state=found;
            }
         }
         if(state!=null && !state.isAir())return true;
      }
      return false;
   }

   private static boolean hasActualRenderedQuads(BlockEntity tile)throws ReflectiveOperationException{
      Object data=findZeroArg(tile.getClass(),"getBlockModelData").invoke(tile);
      if(data==null)return false;
      Class<?> props=Class.forName("mod.chiselsandbits.registrars.ModModelProperties");
      Object key=props.getField("KNOWN_LAYER_MODEL_PROPERTY").get(null);
      Class<?> modelData=Class.forName("com.communi.suggestu.scena.core.client.models.data.IBlockModelData");
      Class<?> keyType=Class.forName("com.communi.suggestu.scena.core.client.models.data.IModelDataKey");
      Object models=modelData.getMethod("getData",keyType).invoke(data,key);
      if(!(models instanceof Map<?,?> layers))return false;
      RandomSource random=RandomSource.create();
      for(Object value:layers.values()){
         if(!(value instanceof BakedModel baked))continue;
         for(Direction face:Direction.values()){
            if(!baked.getQuads(null,face,random).isEmpty())return true;
         }
         if(!baked.getQuads(null,null,random).isEmpty())return true;
      }
      return false;
   }
   private static Method findZeroArg(Class<?> type,String name)throws NoSuchMethodException{
      try{
         // Even a PUBLIC method on a package-private C&B/Scena implementation
         // is not reflectively invocable from this RGB package without
         // accessibility override. getMethod() finds it but invoke() fails.
         // The fallback below already handles protected inherited callbacks.
         Method method=type.getMethod(name);
         method.setAccessible(true);
         return method;
      }
      catch(NoSuchMethodException missing){
         // Some C&B native loaders expose a method on a non-public
         // implementation class. getMethod alone misses the usable API.
         for(Class<?> current=type;current!=null;current=current.getSuperclass()){
            try{
               Method method=current.getDeclaredMethod(name);
               method.setAccessible(true);
               return method;
            }catch(NoSuchMethodException next){
               // Continue up the hierarchy. Never modify voxel state.
            }
         }
         throw missing;
      }
   }

   private static void logOracleFailure(Long id,BlockPos pos,Throwable error){
      if(id==null)return;
      long last=LAST_ORACLE_ERROR.getOrDefault(id,-600L);
      if(ticks-last<600L)return;
      LAST_ORACLE_ERROR.put(id,ticks);
      Throwable cause=error;
      while(cause.getCause()!=null && cause.getCause()!=cause)cause=cause.getCause();
      System.err.println("[RGB Blocks] C&B mesh oracle failed at "+pos+
         " tick="+ticks+" reason="+cause.getClass().getName()+
         ": "+cause.getMessage());
      if(LAST_ORACLE_ERROR.size()>4096)LAST_ORACLE_ERROR.clear();
   }

}
