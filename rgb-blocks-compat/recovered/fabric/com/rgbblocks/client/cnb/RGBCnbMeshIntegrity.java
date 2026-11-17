package com.rgbblocks.client.cnb;

import com.rgbblocks.client.lighting.RGBRenderInvalidator;
import java.lang.reflect.Method;
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
            continue;
         }
         try{
            BlockEntity tile=level.getBlockEntity(pos);
            if(tile==null || tile.isRemoved() ||
              !tile.getClass().getName().contains("chiselsandbits")){
               MISSING.remove(id);
               continue;
            }
            String name=String.valueOf(BuiltInRegistries.BLOCK.getKey(
                 level.getBlockState(pos).getBlock()));
            if(!"chiselsandbits:chiseled".equals(name)){
               MISSING.remove(id);
               continue;
            }
            if(!hasActualVoxelStates(tile)){
               MISSING.remove(id);
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
            REPAIRED.put(id,ticks);
            MISSING.remove(id);
            // Safe on CLIENT game thread, and only for a CURRENT loaded tile.
            // C&B's own async update publishes the model then requests the
            // native chunk renderer to rebuild, preserving RGB baked light.
            RGBCnbGeometryBakeDebouncer.runUndebounced(()->{
               try{
                  Method update=findZeroArg(tile.getClass(),"updateModelData");
                  update.invoke(tile);
                  RGBRenderInvalidator.dirtyAround(pos,2);
                  System.out.println("[RGB Blocks] Restoring missing C&B mesh quads at "
                     +pos+" without modifying RGB or voxel data");
               }catch(Throwable err){
                  System.err.println("[RGB Blocks] C&B mesh integrity refresh failed: "+err);
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
   }

   private static boolean hasActualVoxelStates(BlockEntity tile)throws ReflectiveOperationException{
      Object statistics=findZeroArg(tile.getClass(),"getStatistics").invoke(tile);
      Method method=findZeroArg(statistics.getClass(),"getStateCounts");
      method.setAccessible(true);
      Object counts=method.invoke(statistics);
      if(!(counts instanceof Map<?,?> map))return false;
      for(Object count:map.values())if(count instanceof Number n && n.intValue()>0)return true;
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
      try{return type.getMethod(name);}
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
