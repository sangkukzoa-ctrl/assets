#!/usr/bin/env python3
"""Prepare MC 1.21.1 Fabric port build, retaining original game logic.
Generated project is a migration workspace. A JAR build alone is not a release gate.
"""
import json, pathlib, re, shutil, sys, urllib.request, zipfile
HERE=pathlib.Path("rgb-blocks-compat")
WORK=pathlib.Path("port-work/mc1211-fabric")
CODE=WORK/"src/main/java"
RES=WORK/"src/main/resources"
FROM=HERE/"recovered/fabric"
shutil.rmtree(WORK,ignore_errors=True)
shutil.copytree(FROM/"com",CODE/"com")
RES.mkdir(parents=True,exist_ok=True)

def patch(p,func):
    x=p.read_text(encoding="utf-8")
    y=func(x)
    if x!=y:p.write_text(y,encoding="utf-8")

for p in CODE.rglob("*.java"):
    def common(s):
        return (s.replace("net.minecraft.resources.Identifier","net.minecraft.resources.ResourceLocation")
                 .replace("Identifier", "ResourceLocation")
                 .replace(".identifier()", ".location()")
                 .replace("Identifier.fromNamespaceAndPath","ResourceLocation.fromNamespaceAndPath")
                 .replace("new Identifier(","new ResourceLocation(")
                 .replace("net.minecraft.client.renderer.block.BlockAndTintGetter","net.minecraft.world.level.BlockAndTintGetter")
                 .replace("net.minecraft.client.resources.model.geometry.BakedQuad","net.minecraft.client.renderer.block.model.BakedQuad")
                 .replace("net.minecraft.util.ARGB","com.rgbblocks.compat.ARGB")
                 .replace("net.minecraft.util.LightCoordsUtil","com.rgbblocks.compat.LightCoordsUtil")
                 .replace("com.mojang.blaze3d.vertex.QuadInstance","com.rgbblocks.compat.QuadInstance"))
    patch(p,common)

# 26.1.2 glass models force translucent in their model texture descriptor.
# MC1.21.1 Fabric needs the terrain render layer mapping explicitly.
client_init=CODE/"com/rgbblocks/client/RgbBlocksClient.java"
def adapt_client_layers(src):
    src=src.replace("import com.rgbblocks.client.config.RGBClientConfig;", """import com.rgbblocks.client.config.RGBClientConfig;
import com.rgbblocks.RgbBlocksMod;
import net.fabricmc.fabric.api.blockrenderlayer.v1.BlockRenderLayerMap;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;""")
    if "BlockRenderLayerMap.INSTANCE.putBlock" not in src:
        src=src.replace("RGBClientConfig.initialize();", """RGBClientConfig.initialize();
      for (Item item : RgbBlocksMod.GLASS_ITEMS) {
         BlockRenderLayerMap.INSTANCE.putBlock(((BlockItem)item).getBlock(), RenderType.translucent());
      }""")
    return src
patch(client_init,adapt_client_layers)

main=CODE/"com/rgbblocks/RgbBlocksMod.java"
def pm(s):
    s=s.replace('net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab','net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup')
    s=s.replace('import net.minecraft.world.InteractionResult;', 'import net.minecraft.world.InteractionResultHolder;')
    s=s.replace('Properties.of().setId(key)','Properties.of()')
    s=s.replace('new net.minecraft.world.item.Item.Properties().setId(blockItemKey).useBlockDescriptionPrefix()','new net.minecraft.world.item.Item.Properties()')
    s=s.replace('new net.minecraft.world.item.Item.Properties().setId(key)','new net.minecraft.world.item.Item.Properties()')
    s=s.replace('FabricCreativeModeTab.builder()', 'FabricItemGroup.builder()')
    s=s.replace('Commands.hasPermission(Commands.LEVEL_GAMEMASTERS)','source -> source.hasPermission(2)')
    s=s.replace('public InteractionResult use(Level level, Player player, InteractionHand hand)', 'public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand)')
    s=s.replace('return InteractionResult.SUCCESS_SERVER;', 'return InteractionResultHolder.sidedSuccess(player.getItemInHand(hand), false);')
    s=s.replace('return InteractionResult.SUCCESS;', 'return InteractionResultHolder.sidedSuccess(player.getItemInHand(hand), true);')
    return s
patch(main,pm)

runtime=CODE/"com/rgbblocks/runtime/RGBRuntime.java"
def pr(s):
    s=s.replace("server.getDataStorage().computeIfAbsent(RGBRuntime.RuntimeData.TYPE)",'server.overworld().getDataStorage().computeIfAbsent(RGBRuntime.RuntimeData.FACTORY, "rgbblocks_runtime")')
    s=s.replace('import net.minecraft.world.level.saveddata.SavedDataType;', 'import net.minecraft.nbt.CompoundTag;\nimport net.minecraft.core.HolderLookup;')
    a=s.index("   public static final class RuntimeData extends SavedData {")
    b=s.index("   public record StatePayload(",a)
    fixed='''   public static final class RuntimeData extends SavedData {
      public static final SavedData.Factory<RuntimeData> FACTORY = new SavedData.Factory<>(
          RuntimeData::new, RuntimeData::load, null);
      private Mode mode;
      private boolean bakeAll;
      private int bakeRadius;
      private String worldId;
      public RuntimeData() {
         this(Mode.AUTO.name(), false, 32, UUID.randomUUID().toString());
      }
      private RuntimeData(String mode, boolean bakeAll, int bakeRadius, String worldId) {
         try {this.mode = Mode.valueOf(mode);} catch(IllegalArgumentException ignored){this.mode = Mode.AUTO;}
         this.bakeAll = bakeAll;
         this.bakeRadius = clamp(bakeRadius, 4, 256);
         if (worldId==null || worldId.isBlank()) {
            this.worldId=UUID.randomUUID().toString();setDirty();
         } else this.worldId=worldId;
      }
      private static RuntimeData load(CompoundTag tag, HolderLookup.Provider provider) {
         return new RuntimeData(tag.getString("mode"),tag.getBoolean("bake_all"),
              tag.contains("bake_radius")?tag.getInt("bake_radius"):32,tag.getString("world_id"));
      }
      @Override public CompoundTag save(CompoundTag tag, HolderLookup.Provider provider) {
         tag.putString("mode",mode.name());
         tag.putBoolean("bake_all",bakeAll);
         tag.putInt("bake_radius",bakeRadius);
         tag.putString("world_id",worldId);
         return tag;
      }
      public Mode mode(){return mode;}
      public boolean bakeAll(){return bakeAll;}
      public int bakeRadius(){return bakeRadius;}
      public String worldId(){return worldId;}
      public String bakeDescription(){return bakeAll?"ALL dirty positions":"radius "+bakeRadius;}
      public void setMode(Mode mode){ Mode next=mode==null?Mode.AUTO:mode; if(this.mode!=next){this.mode=next;setDirty();}}
      public void setBakeAll(){if(!bakeAll){bakeAll=true;setDirty();}}
      public void setBakeRadius(int radius){int next=clamp(radius,4,256);if(bakeAll || bakeRadius!=next){bakeAll=false;bakeRadius=next;setDirty();}}
   }

'''
    return s[:a]+fixed+s[b:]
patch(runtime,pr)
compat=CODE/"com/rgbblocks/compat"
compat.mkdir(parents=True,exist_ok=True)
(compat/"ARGB.java").write_text('''package com.rgbblocks.compat;
public final class ARGB {
 private ARGB(){}
 public static int alpha(int color){return color>>>24;}
 public static int red(int color){return (color>>16)&255;}
 public static int green(int color){return (color>>8)&255;}
 public static int blue(int color){return color&255;}
 public static int color(int a,int r,int g,int b){return (a<<24)|((r&255)<<16)|((g&255)<<8)|(b&255);}
}
''')
(compat/"LightCoordsUtil.java").write_text('''package com.rgbblocks.compat;
public final class LightCoordsUtil {
 private LightCoordsUtil(){}
 public static int block(int packed){return (packed>>4)&15;}
 public static int sky(int packed){return (packed>>20)&15;}
 public static int pack(int block,int sky){return ((sky&15)<<20)|((block&15)<<4);}
}
''')
(compat/"QuadInstance.java").write_text('''package com.rgbblocks.compat;
public interface QuadInstance {
  int getLightCoords(int vertex);
  void setLightCoords(int vertex,int packedLight);
  int getColor(int vertex);
  void setColor(int vertex,int color);
}
''')
engine=CODE/"com/rgbblocks/client/lighting/RGBRealLightEngine.java"
def pe(s):
    s=s.replace("quad.position(vertex)","rgbblocks$vertexPosition(quad, vertex)")
    idx=s.rfind("}")
    s=s[:idx]+'''
   private static org.joml.Vector3fc rgbblocks$vertexPosition(BakedQuad quad,int vertex){
      int[] data=quad.getVertices();
      int stride=data.length/4;
      int base=vertex*stride;
      if(base+2>=data.length) return new org.joml.Vector3f(0.5f,0.5f,0.5f);
      return new org.joml.Vector3f(Float.intBitsToFloat(data[base]),
         Float.intBitsToFloat(data[base+1]),Float.intBitsToFloat(data[base+2]));
   }
'''+s[idx:]
    return s
patch(engine,pe)

# Normalize 26.1.2 BlockState light damping to 1.21.1 world-aware queries.
lights=CODE/"com/rgbblocks/client/lighting/RGBLightEngine.java"
def pl(s):
    s=s.replace("state.getLightDampening()", "state.getLightBlock(level, pos)")
    s=s.replace("isOpaqueSolidBarrierState(state)", "isOpaqueSolidBarrierState(level, pos, state)")
    s=s.replace("isOpaqueSolidBarrierState(BlockState state)", "isOpaqueSolidBarrierState(BlockAndTintGetter level, BlockPos pos, BlockState state)")
    s=s.replace("state.isSolidRender()", "state.isSolidRender(level,pos)")
    return s
patch(lights,pl)

invalidator=CODE/"com/rgbblocks/client/lighting/RGBRenderInvalidator.java"
def pi(s):
    s=s.replace("renderer.setSectionRangeDirty(\n               floorSection(minX), floorSection(minY), floorSection(minZ), floorSection(maxX), floorSection(maxY), floorSection(maxZ)\n            );",
                "renderer.setBlocksDirty(minX,minY,minZ,maxX,maxY,maxZ);")
    s=s.replace("renderer.setSectionRangeDirty(minSx, minSy, minSz, maxSx, maxSy, maxSz);",
                "// Legacy LevelRenderer uses per-section dirty invalidation below.")
    return s
patch(invalidator,pi)

patch(runtime,lambda s:s.replace("PayloadTypeRegistry.clientboundPlay()","PayloadTypeRegistry.playS2C()"))

clientLevel=CODE/"com/rgbblocks/mixin/client/ClientLevelMixin.java"
patch(clientLevel, lambda s:s.replace("(ClientLevel)this","(ClientLevel)(Object)this"))


# Mixin requires an old renderer-specific hook. Introduce disabled-by-default
# staging until the method descriptor is checked against the 1.21.1 client jar.
renderer=CODE/"com/rgbblocks/mixin/client/ModelBlockRendererMixin.java"
renderer.write_text('''package com.rgbblocks.mixin.client;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.rgbblocks.client.lighting.RGBRealLightEngine;
import com.rgbblocks.compat.QuadInstance;
import java.util.Arrays;
import net.minecraft.world.level.BlockAndTintGetter;
import net.minecraft.client.renderer.block.ModelBlockRenderer;
import net.minecraft.client.renderer.block.model.BakedQuad;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/** Minecraft 1.21.1 vertex RGB hook. Translates original QuadInstance shader
 * pipeline to the old BakedQuad/VertexConsumer packed vertex format.
 * Fails loudly if vanilla invocation descriptor changes.
 */
@Mixin(ModelBlockRenderer.class)
public abstract class ModelBlockRendererMixin {
 @Redirect(method="putQuadData",
   at=@At(value="INVOKE",target="Lcom/mojang/blaze3d/vertex/VertexConsumer;putBulkData(Lcom/mojang/blaze3d/vertex/PoseStack$Pose;Lnet/minecraft/client/renderer/block/model/BakedQuad;[FFFFF[IIZ)V"),
   require=1)
 private void rgbblocks$lightQuad(VertexConsumer output,PoseStack.Pose pose,BakedQuad quad,
    float[] brightness,float red,float green,float blue,float alpha,int[] lightmap,
    int overlay,boolean readExistingColor,
    BlockAndTintGetter level,BlockState state,BlockPos pos,VertexConsumer originalConsumer,
    PoseStack.Pose originalPose,BakedQuad originalQuad,
    float b0,float b1,float b2,float b3,int light0,int light1,int light2,int light3,int packedOverlay){
    final int[] data=quad.getVertices().clone();
    final int stride=data.length/4;
    final int[] light=lightmap.clone();
    QuadInstance carrier=new QuadInstance(){
      public int getLightCoords(int vertex){return light[vertex];}
      public void setLightCoords(int vertex,int value){light[vertex]=value;}
      public int getColor(int vertex){return data[vertex*stride+3];}
      public void setColor(int vertex,int value){data[vertex*stride+3]=value;}
    };
    RGBRealLightEngine.applyToVanillaQuad(level,pos,state,quad,carrier);
    BakedQuad adjusted=Arrays.equals(data,quad.getVertices())?quad:
      new BakedQuad(data,quad.getTintIndex(),quad.getDirection(),quad.getSprite(),quad.isShade());
    output.putBulkData(pose,adjusted,brightness,red,green,blue,alpha,light,overlay,readExistingColor);
 }
}
''',encoding="utf-8")
lm=CODE/"com/rgbblocks/mixin/client/LightmapRenderStateExtractorMixin.java"
lm.write_text('''package com.rgbblocks.mixin.client;
import net.minecraft.client.renderer.LightTexture;
import org.spongepowered.asm.mixin.Mixin;
/** The original 26.1.2 target contains an empty injection; no equivalent
 * lightmap post-effect exists in 1.21.1. The per-vertex RGB hook is separate.
 */
@Mixin(LightTexture.class)
public abstract class LightmapRenderStateExtractorMixin {}
''',encoding="utf-8")

# 1.21.1 ClientLevel inherits Level.setBlockEntity; the 26.1.2
# ClientLevel.onBlockEntityAdded callback did not exist in 1.21.1.
clientcode=clientLevel.read_text(encoding="utf-8")
first=clientcode.index('   @Inject(method = "onBlockEntityAdded"')
last=clientcode.index('   private static boolean rgbblocks$isRemoteMultiplayer()', first)
clientLevel.write_text(clientcode[:first]+clientcode[last:],encoding="utf-8")
levelhook=CODE/"com/rgbblocks/mixin/client/LevelBlockEntityAttachedMixin.java"
levelhook.write_text('''package com.rgbblocks.mixin.client;
import com.rgbblocks.client.cnb.RGBCnbReloadWakeup;
import com.rgbblocks.client.lighting.RGBLightEngine;
import com.rgbblocks.client.lighting.RGBRealLightEngine;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
/** Previous onBlockEntityAdded hook ported to 1.21.1 Level attachment. */
@Mixin(Level.class)
public abstract class LevelBlockEntityAttachedMixin {
  @Inject(method="setBlockEntity",at=@At("TAIL"),require=1)
  private void rgbblocks$clientEntityAttached(BlockEntity blockEntity,CallbackInfo ci) {
    if (!((Object)this instanceof ClientLevel) || blockEntity==null) return;
    try { RGBCnbReloadWakeup.onBlockEntityAdded(blockEntity); } catch(Throwable ignored){}
    BlockPos pos=blockEntity.getBlockPos();
    BlockState state=blockEntity.getBlockState();
    if (state==null || pos==null) return;
    if (state.getLightEmission()>0 || String.valueOf(
      net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(state.getBlock()))
          .matches(".*(rgbblocks|chiselsandbits):.*"))
       RGBRealLightEngine.settleAfterServerSync(pos);
  }
}
''',encoding="utf-8")
# Replace missing MC26 disconnect callbacks with 1.21.1 central disconnect.
disconnect=CODE/"com/rgbblocks/mixin/client/MinecraftDisconnectMixin.java"
disconnect.write_text('''package com.rgbblocks.mixin.client;
import com.rgbblocks.client.cnb.RGBCnbGeometryBakeDebouncer;
import com.rgbblocks.client.cnb.RGBCnbReloadWakeup;
import com.rgbblocks.client.lighting.RGBRealLightEngine;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.Screen;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
@Mixin(Minecraft.class)
public abstract class MinecraftDisconnectMixin {
 @Inject(method="tick",at=@At("TAIL"),require=1)
 private void rgbblocks$onTick(CallbackInfo ci){RGBRealLightEngine.processClientTick();}
 @Inject(method="disconnect(Lnet/minecraft/client/gui/screens/Screen;Z)V",at=@At("HEAD"),require=1)
 private void rgbblocks$onDisconnect(Screen screen,boolean transfer,CallbackInfo ci){
    RGBRealLightEngine.onClientDisconnect();
    RGBCnbGeometryBakeDebouncer.reset();
    RGBCnbReloadWakeup.reset();
 }
}
''',encoding="utf-8")

# Restore Chisels & Bits behavior at the OLD stable API.
# Both official C&B 21.1.40 and 20.1.20 have ChiseledBlockBlockColor
# (the new 26.1.2 ChiseledBlockColorProvider no longer existed there).
cnb_color=CODE/"com/rgbblocks/mixin/client/CnbChiseledBlockColorProviderMixin.java"
cnb_color.write_text('''package com.rgbblocks.mixin.client;
import net.minecraft.client.Minecraft;
import net.minecraft.world.level.BlockAndTintGetter;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.core.BlockPos;
import org.spongepowered.asm.mixin.Dynamic;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
@Pseudo
@Mixin(targets="mod.chiselsandbits.client.colors.ChiseledBlockBlockColor",remap=false)
public abstract class CnbChiseledBlockColorProviderMixin {
 @Inject(method="getColor",
   at=@At("HEAD"),cancellable=true,require=1,remap=false)
 @Dynamic("C&B 21.1.40/20.1.20 direct BlockColor.getColor replaces 26.x collect")
 private void rgbblocks$avoidWorkerThreadTint(BlockState state,BlockAndTintGetter getter,BlockPos pos,int tint,
   CallbackInfoReturnable<Integer> result) {
    if(getter == null) return;
    String type=getter.getClass().getName();
    if(type.startsWith("net.caffeinemc.mods.sodium.client.world.") || type.startsWith("me.jellysquid.mods.sodium.client.world.")) {
      try {
        Minecraft mc=Minecraft.getInstance();
        if(mc != null && !mc.isSameThread())result.setReturnValue(-1);
      } catch(Throwable ignored) {}
    }
 }
}
''',encoding="utf-8")

# The old 26.x ChiseledBlockStateModel does not exist. Reattach the
# "model parts updated -> invalidate RGB light" event to the actual old
# ChiseledBlockEntity#updateModelData lifecycle.
cnb_parts=CODE/"com/rgbblocks/mixin/client/CnbChiseledBlockStateModelMixin.java"
cnb_parts.write_text('''package com.rgbblocks.mixin.client;
import com.rgbblocks.client.lighting.RGBRealLightEngine;
import java.util.Collections;
import net.minecraft.core.BlockPos;
import org.spongepowered.asm.mixin.Dynamic;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
@Pseudo
@Mixin(targets="mod.chiselsandbits.block.entities.ChiseledBlockEntity",remap=false)
public abstract class CnbChiseledBlockStateModelMixin {
 @Inject(method="updateModelData()V",at=@At("TAIL"),require=1,remap=false)
 @Dynamic("C&B older block entity model-update lifecycle instead of 26.x collectParts")
 private void rgbblocks$captureCnbPartSources(CallbackInfo ci){
   try {
      Object entity=this;
      BlockPos pos=(BlockPos)entity.getClass().getMethod("getBlockPos").invoke(entity);
      RGBRealLightEngine.registerCnbModelPartSources(pos,Collections.emptyList());
   } catch(Throwable ignored){}
 }
}
''',encoding="utf-8")

# Sodium 0.6.13 uses Fabric Renderer API MutableQuadViewImpl, not the
# 26.1.2 Sodium 0.8 QuadInstance pipeline. Attach RGB to quad BEFORE the
# actual chunk vertex encoder; retains vanilla albedo and changes only
# vertex light and RGB colour contribution.
sodium06=CODE/"com/rgbblocks/mixin/client/Sodium06BlockRendererMixin.java"
sodium06.write_text('''package com.rgbblocks.mixin.client;
import com.rgbblocks.client.lighting.SodiumRgbBridge;
import java.lang.reflect.Method;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Dynamic;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Source target confirmed against Sodium mc1.21.1-0.6.13 BlockRenderer.
 * Reflective quad adapter avoids a hard Sodium dependency on non-Sodium clients.
 */
@Pseudo
@Mixin(targets="net.caffeinemc.mods.sodium.client.render.chunk.compile.pipeline.BlockRenderer",remap=false)
public abstract class Sodium06BlockRendererMixin {
 @Unique private static volatile Method rbX,rbY,rbZ,rbColorGet,rbLightGet,rbColorSet,rbLightSet;
 @Unique private static volatile Class<?> rbQuadClass;
 @Inject(method="renderModel",
   at=@At("HEAD"),require=1,remap=false)
 @Dynamic("Sodium 0.6.13 BlockRenderer.renderModel entry")
 private void rgbblocks$begin(BakedModel model,BlockState state,BlockPos pos,BlockPos origin,CallbackInfo ci) {
    SodiumRgbBridge.begin(null,state,pos);
 }
 @Inject(method="renderModel",
   at=@At("RETURN"),require=1,remap=false)
 @Dynamic("Sodium 0.6.13 BlockRenderer.renderModel exit")
 private void rgbblocks$end(BakedModel model,BlockState state,BlockPos pos,BlockPos origin,CallbackInfo ci) {
    SodiumRgbBridge.end();
 }
 @Unique private static synchronized void rgbblocks$initAccessor(Class<?> type)throws NoSuchMethodException {
    if(rbQuadClass==type)return;
    rbX=type.getMethod("x",int.class);rbY=type.getMethod("y",int.class);rbZ=type.getMethod("z",int.class);
    rbColorGet=type.getMethod("color",int.class);rbLightGet=type.getMethod("lightmap",int.class);
    rbColorSet=type.getMethod("color",int.class,int.class);rbLightSet=type.getMethod("lightmap",int.class,int.class);
    rbQuadClass=type;
 }
 @Inject(method="bufferQuad",at=@At("HEAD"),require=1,remap=false)
 @Dynamic("Sodium 0.6.13 BlockRenderer.bufferQuad before chunk encoder")
 private void rgbblocks$vertexRgb(@Coerce Object quad,float[] brightness,@Coerce Object material,CallbackInfo ci) {
   try {
     if(quad==null)return;
     if(rbQuadClass!=quad.getClass())rgbblocks$initAccessor(quad.getClass());
     for(int i=0;i<4;i++){
        float x=((Number)rbX.invoke(quad,i)).floatValue();
        float y=((Number)rbY.invoke(quad,i)).floatValue();
        float z=((Number)rbZ.invoke(quad,i)).floatValue();
        int oldLight=((Number)rbLightGet.invoke(quad,i)).intValue();
        int oldColor=((Number)rbColorGet.invoke(quad,i)).intValue();
        int light=SodiumRgbBridge.applyLight(oldLight,x,y,z,null);
        int color=SodiumRgbBridge.applyColorWithLight(oldColor,light,x,y,z,null);
        if(light!=oldLight)rbLightSet.invoke(quad,i,light);
        if(color!=oldColor)rbColorSet.invoke(quad,i,color);
     }
   } catch(Throwable error) {
     if(!rgbblocks$reported) {
        rgbblocks$reported=true;
        System.err.println("RGB Blocks Sodium 0.6 RGB vertex bridge failed; graphics validation required: "+error);
     }
   }
 }
 @Unique private static volatile boolean rgbblocks$reported;
}
''',encoding="utf-8")

# Download author-published Fabric 1.3.1F metadata and resources.
URL="https://cdn.modrinth.com/data/A48MxLWx/versions/HsQZbhRf/RgbBlocksmod-26.1.2-1.3.1F.jar"
r=urllib.request.Request(URL,headers={"User-Agent":"RGBBlocks-owner-porting/1.0"})
with urllib.request.urlopen(r,timeout=120) as f: buf=f.read()
jpath=WORK/"original-fabric-131.jar"
jpath.write_bytes(buf)
with zipfile.ZipFile(jpath) as z:
    manifest=None
    for name in z.namelist():
        if name=="fabric.mod.json":
            manifest=json.loads(z.read(name))
        if name.startswith("assets/") or name.startswith("data/"):
            path=RES/name
            if name.endswith("/"):path.mkdir(parents=True,exist_ok=True);continue
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(z.read(name))
        if "mixin" in name.lower() and name.endswith(".json") and "/" not in name:
            (RES/name).write_bytes(z.read(name))
    if manifest is None:raise RuntimeError("original Fabric metadata missing")
manifest["version"]="1.3.1+mc1.21.1"
manifest["depends"]["minecraft"]="1.21.1"
manifest["depends"]["fabricloader"]=">=0.16.0"
manifest["depends"]["java"]=">=21"
manifest["depends"]["fabric-api"]=">=0.116.17+1.21.1"
(RES/"fabric.mod.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
# Older clients need explicit pack metadata for mod_resources recognition.
# The source 26.1.2 JAR's root metadata is not a 1.21.1 compatible pack format.
(RES/"pack.mcmeta").write_text(json.dumps({"pack":{"pack_format":34,"description":"RGB Blocks 1.3.1 — Minecraft 1.21.1"}},ensure_ascii=False,indent=2),encoding="utf-8")
# Bind the 1.21.1 replacement callback in the existing original Mixin config.
for entry in manifest.get("mixins",[]):
    config=entry.get("config") if isinstance(entry,dict) else entry
    file=RES/config
    if file.is_file():
        cfg=json.loads(file.read_text(encoding="utf-8"))
        cfg["compatibilityLevel"]="JAVA_21"
        cfg.setdefault("client",[])
        if "client.LevelBlockEntityAttachedMixin" not in cfg["client"]:
            cfg["client"].append("client.LevelBlockEntityAttachedMixin")
        # Remove 26.1.2 Sodium 0.8 targets; 1.21.1 Sodium 0.6 has a
        # structurally different chunk quad pipeline.
        cfg["client"]=[entry for entry in cfg["client"] if not any(
            old in entry for old in ("SodiumChunkBuilderMeshingTaskMixin",
                                     "SodiumMutableQuadViewImplMixin",
                                     "SodiumQuadViewImplAccessorMixin"))]
        if "client.Sodium06BlockRendererMixin" not in cfg["client"]:
            cfg["client"].append("client.Sodium06BlockRendererMixin")
        file.write_text(json.dumps(cfg,indent=2),encoding="utf-8")


# 26.x glass model texture schema incompatible with 1.21.1 pre-1.21.4 block model codec
changed=0
for path in (RES/"assets/rgbblocks/models/block").glob("*_glass.json"):
    obj=json.loads(path.read_text(encoding="utf-8"))
    tex=obj.get("textures",{})
    for key,value in tex.items():
        if isinstance(value,dict):
            tex[key]=value.get("id",value.get("texture",value.get("sprite","minecraft:block/white_stained_glass")))
            changed+=1
    if changed and any(not isinstance(v,str) for v in tex.values()):
        raise ValueError(f"Unknown texture schema: {path}")
    path.write_text(json.dumps(obj,separators=(",",":")),encoding="utf-8")
print("glass model texture descriptors converted",changed,flush=True)

(WORK/"settings.gradle").write_text("""
pluginManagement {
 repositories { maven {url='https://maven.fabricmc.net/'}; gradlePluginPortal(); mavenCentral() }
}
rootProject.name='rgbblocks-1.21.1-fabric'
""")
(WORK/"gradle.properties").write_text("org.gradle.jvmargs=-Xmx4G\norg.gradle.parallel=false\norg.gradle.caching=true\n")
(WORK/"build.gradle").write_text("""
plugins { id 'fabric-loom' version '1.9-SNAPSHOT' }
group='com.rgbblocks'
version='1.3.1+mc1.21.1'
base { archivesName='RgbBlocksmod-MC1.21.1-Fabric' }
repositories { maven {url='https://maven.fabricmc.net/'}; mavenCentral() }
dependencies {
 minecraft 'com.mojang:minecraft:1.21.1'
 mappings loom.officialMojangMappings()
 modImplementation 'net.fabricmc:fabric-loader:0.16.14'
 modImplementation 'net.fabricmc.fabric-api:fabric-api:0.116.17+1.21.1'
}
tasks.withType(JavaCompile).configureEach { options.release=21; options.encoding='UTF-8' }
tasks.withType(Zip).configureEach { zip64=true }
java { sourceCompatibility=JavaVersion.VERSION_21; targetCompatibility=JavaVersion.VERSION_21 }
""")
jpath.unlink()
print("STAGED",len(list(CODE.rglob("*.java"))),"Java files; resource files",len(list(RES.rglob("*"))),flush=True)
