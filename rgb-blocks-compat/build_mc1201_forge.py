#!/usr/bin/env python3
"""Build candidate RGB Blocks 1.3.1 for Minecraft 1.20.1 Forge.
Uses recovered owner's original 1.3.1 Fabric logic plus 1.21.1 intermediate
API compatibility as a source baseline. NOT releasable until server/client,
RGB light, C&B and shader tests all pass.
"""
import pathlib,shutil,json,re
WORK=pathlib.Path("port-work/mc1201-forge")
BASE=pathlib.Path("port-work/mc1211-fabric")
if not BASE.exists():
    raise RuntimeError("First generate the 1.21.1 Fabric intermediate source workspace")
shutil.rmtree(WORK,ignore_errors=True)
CODE=WORK/"src/main/java"
RES=WORK/"src/main/resources"
shutil.copytree(BASE/"src/main/java",CODE)
shutil.copytree(BASE/"src/main/resources",RES)
(RES/"fabric.mod.json").unlink(missing_ok=True)

def patch(p,transform):
    x=p.read_text(encoding="utf-8")
    y=transform(x)
    if x!=y:p.write_text(y,encoding="utf-8")

mod=CODE/"com/rgbblocks/RgbBlocksMod.java"
mod.write_text('''package com.rgbblocks;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.rgbblocks.runtime.RGBRuntime;
import java.io.*;
import java.lang.reflect.Type;
import java.nio.charset.StandardCharsets;
import java.util.*;
import net.minecraft.commands.*;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.*;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.*;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;
import net.minecraft.world.level.material.MapColor;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.registries.*;

@Mod(RgbBlocksMod.MODID)
public final class RgbBlocksMod {
 public static final String MODID="rgbblocks";
 public static final DeferredRegister<Block> BLOCKS=DeferredRegister.create(ForgeRegistries.BLOCKS,MODID);
 public static final DeferredRegister<Item> ITEMS=DeferredRegister.create(ForgeRegistries.ITEMS,MODID);
 public static final DeferredRegister<CreativeModeTab> TABS=DeferredRegister.create(Registries.CREATIVE_MODE_TAB,MODID);
 public static final List<RegistryObject<Item>> NORMAL_ITEMS=new ArrayList<>();
 public static final List<RegistryObject<Item>> GLOW_ITEMS=new ArrayList<>();
 public static final List<RegistryObject<Item>> GLASS_ITEMS=new ArrayList<>();
 public static final RegistryObject<Item> RGB_LIGHT_SWITCH=ITEMS.register("rgb_light_switch",()->new RGBModeSwitchItem(new Item.Properties()));
 public static final RegistryObject<Item> RGB_LIGHT_BAKER=ITEMS.register("rgb_light_baker",()->new RGBLightBakerItem(new Item.Properties()));
 static {
    TABS.register("rgb_normal_tab",()->CreativeModeTab.builder()
       .title(Component.literal("RGB Normal")).icon(()->new ItemStack(Items.STONE))
       .displayItems((p,out)->NORMAL_ITEMS.forEach(i->out.accept(i.get()))).build());
    TABS.register("rgb_glow_tab",()->CreativeModeTab.builder()
       .title(Component.literal("RGB Glow")).icon(()->new ItemStack(Items.GLOWSTONE))
       .displayItems((p,out)->GLOW_ITEMS.forEach(i->out.accept(i.get()))).build());
    TABS.register("rgb_glass_tab",()->CreativeModeTab.builder()
       .title(Component.literal("RGB Glass")).icon(()->new ItemStack(Items.GLASS))
       .displayItems((p,out)->GLASS_ITEMS.forEach(i->out.accept(i.get()))).build());
    TABS.register("rgb_tools_tab",()->CreativeModeTab.builder()
       .title(Component.literal("RGB Tools")).icon(()->new ItemStack(RGB_LIGHT_SWITCH.get()))
       .displayItems((p,out)->{out.accept(RGB_LIGHT_SWITCH.get());out.accept(RGB_LIGHT_BAKER.get());}).build());
 }
 public RgbBlocksMod(){
    int count=registerRGBBlocks();
    IEventBus bus=FMLJavaModLoadingContext.get().getModEventBus();
    BLOCKS.register(bus);ITEMS.register(bus);TABS.register(bus);
    RGBRuntime.registerPackets();
    MinecraftForge.EVENT_BUS.addListener(this::onCommands);
    MinecraftForge.EVENT_BUS.addListener(this::onLogin);
    System.out.println("RGB Blocks Forge 1.20.1 registered "+count+" palette colors / "+count*3+" RGB blocks");
 }
 private static RegistryObject<Item> registerColor(String id,java.util.function.Supplier<? extends Block> factory){
    RegistryObject<Block> block=BLOCKS.register(id,factory);
    return ITEMS.register(id,()->new BlockItem(block.get(),new Item.Properties()));
 }
 private static int registerRGBBlocks(){
    try(InputStream stream=RgbBlocksMod.class.getClassLoader().getResourceAsStream("assets/rgbblocks/palette.json")){
       if(stream==null)throw new IllegalStateException("Missing RGB palette.json");
       try(Reader reader=new InputStreamReader(stream,StandardCharsets.UTF_8)){
         Type type=new TypeToken<List<ColorData>>(){}.getType();
         List<ColorData> colors=new Gson().fromJson(reader,type);
         if(colors==null || colors.isEmpty())throw new IllegalStateException("RGB palette empty");
         for(ColorData c:colors){
            String base="rgb_"+c.group+"_"+c.red+"_"+c.green+"_"+c.blue;
            NORMAL_ITEMS.add(registerColor(base,()->new Block(BlockBehaviour.Properties.of().mapColor(MapColor.STONE))));
            GLOW_ITEMS.add(registerColor(base+"_glow",()->new Block(BlockBehaviour.Properties.of().mapColor(MapColor.STONE).lightLevel(state->15))));
            GLASS_ITEMS.add(registerColor(base+"_glass",()->new StainedGlassBlock(DyeColor.WHITE,
                BlockBehaviour.Properties.of().mapColor(MapColor.NONE).instrument(NoteBlockInstrument.HAT)
                 .strength(0.3F).sound(SoundType.GLASS).noOcclusion()
                 .isValidSpawn((state,level,pos,entity)->false)
                 .isRedstoneConductor((state,level,pos)->false)
                 .isSuffocating((state,level,pos)->false)
                 .isViewBlocking((state,level,pos)->false))));
         }
         return colors.size();
       }
    }catch(IOException ex){throw new IllegalStateException("RGB palette registration failed",ex);}
 }
 private static final class ColorData {String group;int red,green,blue;}
 private void onLogin(PlayerEvent.PlayerLoggedInEvent evt){
    if(evt.getEntity() instanceof ServerPlayer player)RGBRuntime.sendState(player);
 }
 private void onCommands(RegisterCommandsEvent evt){registerCommands(evt.getDispatcher());}
 private static void registerCommands(CommandDispatcher<CommandSourceStack> d){
   d.register(Commands.literal("rgb").requires(s->s.hasPermission(2))
    .then(Commands.literal("auto").executes(c->{
       RGBRuntime.setMode(c.getSource().getServer(),RGBRuntime.Mode.AUTO);
       c.getSource().sendSuccess(()->Component.literal("RGB mode: AUTO"),true);return 1;}))
    .then(Commands.literal("manual").executes(c->{
       RGBRuntime.setMode(c.getSource().getServer(),RGBRuntime.Mode.MANUAL);
       c.getSource().sendSuccess(()->Component.literal("RGB mode: MANUAL"),true);return 1;}))
    .then(Commands.literal("bake").executes(c->{
       RGBRuntime.RuntimeData data=RGBRuntime.data(c.getSource().getServer());
       RGBRuntime.broadcastBake(c.getSource().getServer());
       c.getSource().sendSuccess(()->Component.literal("RGB bake requested ("+data.bakeDescription()+")."),true);return 1;
     }).then(Commands.literal("get").executes(c->sendRgbStatus(c.getSource().getServer(),c.getSource()))))
    .then(Commands.literal("get").executes(c->sendRgbStatus(c.getSource().getServer(),c.getSource())))
    .then(Commands.literal("setbake")
     .then(Commands.literal("all").executes(c->{
       RGBRuntime.setBakeAll(c.getSource().getServer());
       c.getSource().sendSuccess(()->Component.literal("RGB bake range: ALL dirty positions"),true);return 1;}))
     .then(Commands.argument("radius",IntegerArgumentType.integer(4,256)).executes(c->{
       int radius=IntegerArgumentType.getInteger(c,"radius");
       RGBRuntime.setBakeRadius(c.getSource().getServer(),radius);
       c.getSource().sendSuccess(()->Component.literal("RGB bake radius: "+radius),true);return 1;}))));
 }
 private static int sendRgbStatus(MinecraftServer server,CommandSourceStack source){
    RGBRuntime.RuntimeData data=RGBRuntime.data(server);
    String scope=data.bakeAll()?"ALL":"RADIUS "+data.bakeRadius();
    source.sendSuccess(()->Component.literal("RGB mode: "+data.mode().name()+" | Bake scope: "+scope+" | World ID: "+data.worldId()),false);
    return 1;
 }
 private static final class RGBLightBakerItem extends Item {
    private RGBLightBakerItem(Item.Properties p){super(p);}
    @Override public InteractionResultHolder<ItemStack> use(Level level,Player player,InteractionHand hand){
      if(level instanceof ServerLevel serverLevel){
        RGBRuntime.RuntimeData data=RGBRuntime.data(serverLevel.getServer());
        RGBRuntime.broadcastBake(serverLevel.getServer());
        if(player instanceof ServerPlayer sp)sp.sendSystemMessage(Component.literal("RGB bake requested ("+data.bakeDescription()+")."),true);
      }
      return InteractionResultHolder.sidedSuccess(player.getItemInHand(hand),level.isClientSide);
    }
 }
 private static final class RGBModeSwitchItem extends Item {
    private RGBModeSwitchItem(Item.Properties p){super(p);}
    @Override public InteractionResultHolder<ItemStack> use(Level level,Player player,InteractionHand hand){
      if(level instanceof ServerLevel serverLevel){
        RGBRuntime.Mode mode=RGBRuntime.toggleMode(serverLevel.getServer());
        if(player instanceof ServerPlayer sp)sp.sendSystemMessage(Component.literal("RGB mode: "+mode.name()),true);
      }
      return InteractionResultHolder.sidedSuccess(player.getItemInHand(hand),level.isClientSide);
    }
 }
}
''',encoding="utf-8")

runtime=CODE/"com/rgbblocks/runtime/RGBRuntime.java"
def network1201(s):
    s=s.replace('import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;','''import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.simple.SimpleChannel;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.network.NetworkEvent;
import java.util.function.Supplier;''')
    s=s.replace('import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;','')
    s=s.replace('import net.minecraft.network.protocol.common.custom.CustomPacketPayload;','')
    s=s.replace('import net.minecraft.network.protocol.common.custom.CustomPacketPayload.Type;','')
    s=s.replace('import net.minecraft.network.codec.StreamCodec;','')
    s=s.replace('import net.minecraft.core.HolderLookup;','')
    start=s.index('   public static void registerPayloadTypes()')
    end=s.index('   public static void acceptState(',start)
    replacement='''   private static final String PROTOCOL="1";
   private static final SimpleChannel CHANNEL=NetworkRegistry.newSimpleChannel(
       new ResourceLocation("rgbblocks","runtime"),()->PROTOCOL,PROTOCOL::equals,PROTOCOL::equals);
   public static void registerPackets(){
      CHANNEL.registerMessage(0,StatePayload.class,
        (msg,buf)->{buf.writeBoolean(msg.auto);buf.writeBoolean(msg.bakeAll);buf.writeInt(msg.bakeRadius);buf.writeUtf(msg.worldId==null?"":msg.worldId);},
        buf->new StatePayload(buf.readBoolean(),buf.readBoolean(),buf.readInt(),buf.readUtf()),
        (msg,context)->{context.get().enqueueWork(()->acceptState(msg));context.get().setPacketHandled(true);});
      CHANNEL.registerMessage(1,BakePayload.class,
        (msg,buf)->{buf.writeBoolean(msg.all);buf.writeInt(msg.radius);},
        buf->new BakePayload(buf.readBoolean(),buf.readInt()),
        (msg,context)->{context.get().enqueueWork(()->acceptBake(msg));context.get().setPacketHandled(true);});
   }
   public static void sendState(ServerPlayer player){
      MinecraftServer server=player.level().getServer();
      if(server!=null){
          RuntimeData data=data(server);
          CHANNEL.send(PacketDistributor.PLAYER.with(()->player),
             new StatePayload(data.mode()==Mode.AUTO,data.bakeAll(),data.bakeRadius(),data.worldId()));
      }
   }
   public static void broadcastState(MinecraftServer server){
      RuntimeData data=data(server);
      StatePayload payload=new StatePayload(data.mode()==Mode.AUTO,data.bakeAll(),data.bakeRadius(),data.worldId());
      for(ServerPlayer player:server.getPlayerList().getPlayers())
         CHANNEL.send(PacketDistributor.PLAYER.with(()->player),payload);
   }
   public static void broadcastBake(MinecraftServer server){
      RuntimeData data=data(server);
      BakePayload payload=new BakePayload(data.bakeAll(),data.bakeRadius());
      for(ServerPlayer player:server.getPlayerList().getPlayers())
         CHANNEL.send(PacketDistributor.PLAYER.with(()->player),payload);
   }

'''
    s=s[:start]+replacement+s[end:]
    start=s.index('   public record BakePayload(')
    end=s.index('   public record BakeRequest(',start)
    s=s[:start]+'''   public record BakePayload(boolean all,int radius) {}
''' +s[end:]
    start=s.index('   public record StatePayload(')
    s=s[:start]+'''   public record StatePayload(boolean auto, boolean bakeAll,int bakeRadius,String worldId) {}
}
'''
    s=s.replace('server.overworld().getDataStorage().computeIfAbsent(RGBRuntime.RuntimeData.FACTORY, "rgbblocks_runtime")','server.overworld().getDataStorage().computeIfAbsent(RGBRuntime.RuntimeData::load,RGBRuntime.RuntimeData::new, "rgbblocks_runtime")')
    s=s.replace('''      public static final SavedData.Factory<RuntimeData> FACTORY = new SavedData.Factory<>(
          RuntimeData::new, RuntimeData::load, null);
''','')
    s=s.replace('private static RuntimeData load(CompoundTag tag, HolderLookup.Provider provider)','public static RuntimeData load(CompoundTag tag)')
    s=s.replace('public CompoundTag save(CompoundTag tag, HolderLookup.Provider provider)','public CompoundTag save(CompoundTag tag)')
    return s
patch(runtime,network1201)

config=CODE/"com/rgbblocks/client/config/RGBClientConfig.java"
patch(config,lambda s:s.replace("net.fabricmc.loader.api.FabricLoader","net.minecraftforge.fml.loading.FMLPaths")
    .replace("FabricLoader.getInstance().getConfigDir()","FMLPaths.CONFIGDIR.get()"))
client=CODE/"com/rgbblocks/client/RgbBlocksClient.java"
client.write_text('''package com.rgbblocks.client;
import com.rgbblocks.client.config.RGBClientConfig;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;
@Mod.EventBusSubscriber(modid="rgbblocks",bus=Mod.EventBusSubscriber.Bus.MOD,value=Dist.CLIENT)
public final class RgbBlocksClient {
 private RgbBlocksClient(){}
 @SubscribeEvent public static void onClientSetup(FMLClientSetupEvent event){
    event.enqueueWork(RGBClientConfig::initialize);
 }
}
''',encoding="utf-8")

# The original lighting math, per-color logic, world persistence and C&B
# listeners remain untouched aside from true 1.20.1 method API migrations.
for p in CODE.rglob("*.java"):
    if p in [mod,runtime,client,config]:continue
    patch(p,lambda s:s.replace('net.fabricmc.loader.api.FabricLoader','net.minecraftforge.fml.loading.FMLPaths')
                        .replace('FabricLoader.getInstance().getConfigDir()','FMLPaths.CONFIGDIR.get()'))

# Per-vertex vanilla RGB 1.20.1: return path is the pre-alpha
# VertexConsumer.putBulkData overload; do not erase RGB tint or light.
renderer=CODE/"com/rgbblocks/mixin/client/ModelBlockRendererMixin.java"
s=renderer.read_text(encoding="utf-8")
s=s.replace('Lnet/minecraft/client/renderer/block/model/BakedQuad;[FFFFF[IIZ)V',
            'Lnet/minecraft/client/renderer/block/model/BakedQuad;[FFFF[IIZ)V')
s=s.replace('float[] brightness,float red,float green,float blue,float alpha,int[] lightmap',
            'float[] brightness,float red,float green,float blue,int[] lightmap')
s=s.replace('brightness,red,green,blue,alpha,light,overlay,readExistingColor',
            'brightness,red,green,blue,light,overlay,readExistingColor')
renderer.write_text(s,encoding="utf-8")

# 1.20.1 Minecraft.disconnect(Screen) has no boolean second parameter.
disconnect=CODE/"com/rgbblocks/mixin/client/MinecraftDisconnectMixin.java"
patch(disconnect, lambda s:s.replace("disconnect(Lnet/minecraft/client/gui/screens/Screen;Z)V",
    "disconnect(Lnet/minecraft/client/gui/screens/Screen;)V")
    .replace("Screen screen,boolean transfer,CallbackInfo ci","Screen screen,CallbackInfo ci"))

# Forge 1.20.1 lifecycle supplies a stable logout event; do not inject into
# a Minecraft.disconnect overload that does not exist in this version.
disconnect=CODE/"com/rgbblocks/mixin/client/MinecraftDisconnectMixin.java"
disconnect.write_text('''package com.rgbblocks.mixin.client;
import com.rgbblocks.client.lighting.RGBRealLightEngine;
import net.minecraft.client.Minecraft;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
@Mixin(Minecraft.class)
public abstract class MinecraftDisconnectMixin {
 @Inject(method="tick",at=@At("TAIL"),require=1)
 private void rgbblocks$onTick(CallbackInfo ci){
   RGBRealLightEngine.processClientTick();
 }
}
''',encoding="utf-8")
forgeEvents=CODE/"com/rgbblocks/client/RGBForgeLogoutEvents.java"
forgeEvents.write_text('''package com.rgbblocks.client;
import com.rgbblocks.client.cnb.RGBCnbGeometryBakeDebouncer;
import com.rgbblocks.client.cnb.RGBCnbReloadWakeup;
import com.rgbblocks.client.lighting.RGBRealLightEngine;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ClientPlayerNetworkEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
@Mod.EventBusSubscriber(modid="rgbblocks", value=Dist.CLIENT)
public final class RGBForgeLogoutEvents {
  private RGBForgeLogoutEvents(){}
  @SubscribeEvent public static void loggedOut(ClientPlayerNetworkEvent.LoggingOut event) {
    RGBRealLightEngine.onClientDisconnect();
    RGBCnbGeometryBakeDebouncer.reset();
    RGBCnbReloadWakeup.reset();
  }
}
''',encoding="utf-8")

# Java 17: old code's pattern matching on BlockAndTintGetter->BlockGetter
# fails because the superinterface is always implemented.
rgbengine=CODE/"com/rgbblocks/client/lighting/RGBRealLightEngine.java"
patch(rgbengine,lambda s:s.replace(
 "if (clientLevel() instanceof BlockGetter getter) {",
 "BlockGetter getter = clientLevel();\\n         if (getter != null) {".replace("\\n","\n")))

# Convert original Fabric MixinPlugin early mod-discovery to Forge-loading
# registry; this plugin runs before standard ModList initialization.
plugin=CODE/"com/rgbblocks/mixin/RGBBlocksMixinPlugin.java"
def forge_plugin(s):
    s=s.replace("import net.minecraftforge.fml.loading.FMLPaths;",
                "import net.minecraftforge.fml.loading.FMLLoader;")
    s=s.replace("import net.fabricmc.loader.api.FabricLoader;",
                "import net.minecraftforge.fml.loading.FMLLoader;")
    s=s.replace('FabricLoader.getInstance().isModLoaded("chiselsandbits")',
                'FMLLoader.getLoadingModList().getModFileById("chiselsandbits") != null')
    s=s.replace('FabricLoader.getInstance().isModLoaded("sodium")',
                'FMLLoader.getLoadingModList().getModFileById("embeddium") != null')
    return s
patch(plugin,forge_plugin)

# Embeddium 0.3.31 is based on Sodium 0.5.8, not the 0.6/0.8
# APIs. Exact method descriptor and vertex array schema were checked against
# official modrinth release UTbfe5d1 with javap in GitHub Actions.
emb=CODE/"com/rgbblocks/mixin/client/Embeddium03BlockRendererMixin.java"
emb.write_text('''package com.rgbblocks.mixin.client;
import com.rgbblocks.client.lighting.SodiumRgbBridge;
import java.lang.reflect.*;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockAndTintGetter;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Dynamic;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Embeddium 0.3.31 Forge 1.20.1 RGB per-vertex hook.
 * Original 26.1.2 light math remains in SodiumRgbBridge/RGBRealLightEngine.
 * Intercepts the actual 0.3.31 writeGeometry before light/color packing.
 */
@Pseudo
@Mixin(targets="me.jellysquid.mods.sodium.client.render.chunk.compile.pipeline.BlockRenderer",remap=false)
public abstract class Embeddium03BlockRendererMixin {
 @Unique private static volatile Method rbContextPos,rbContextState,rbContextLevel;
 @Unique private static volatile Method rbGetX,rbGetY,rbGetZ;
 @Unique private static volatile Field rbLightsField;
 @Unique private static volatile Class<?> rbContextClass,rbQuadClass,rbLightClass;
 @Unique private static volatile boolean rbReported;
 @Unique private static synchronized void rbResolveCtx(Class<?> type)throws ReflectiveOperationException{
    if(rbContextClass==type)return;
    rbContextPos=type.getMethod("pos");
    rbContextState=type.getMethod("state");
    rbContextLevel=type.getMethod("localSlice");
    rbContextClass=type;
 }
 @Unique private static synchronized void rbResolveQuad(Class<?> type)throws ReflectiveOperationException{
    if(rbQuadClass==type)return;
    rbGetX=type.getMethod("getX",int.class);
    rbGetY=type.getMethod("getY",int.class);
    rbGetZ=type.getMethod("getZ",int.class);
    rbQuadClass=type;
 }
 @Unique private static synchronized void rbResolveLight(Class<?> type)throws ReflectiveOperationException{
    if(rbLightClass==type)return;
    rbLightsField=type.getField("lm");
    rbLightClass=type;
 }
 @Inject(method="renderModel",at=@At("HEAD"),require=1,remap=false)
 @Dynamic("Embeddium 0.3.31 BlockRenderer.renderModel(BlockRenderContext,ChunkBuildBuffers)")
 private void rgbblocks$begin(@Coerce Object context,@Coerce Object buffers,CallbackInfo ci){
    try {
      if(rbContextClass!=context.getClass())rbResolveCtx(context.getClass());
      BlockAndTintGetter world=(BlockAndTintGetter)rbContextLevel.invoke(context);
      BlockState state=(BlockState)rbContextState.invoke(context);
      BlockPos pos=(BlockPos)rbContextPos.invoke(context);
      SodiumRgbBridge.begin(world,state,pos);
    }catch(Throwable failure){rbReport(failure);}
 }
 @Inject(method="renderModel",at=@At("RETURN"),require=1,remap=false)
 private void rgbblocks$end(@Coerce Object context,@Coerce Object buffers,CallbackInfo ci){
    SodiumRgbBridge.end();
 }
 @Inject(method="writeGeometry",at=@At("HEAD"),require=1,remap=false)
 @Dynamic("Embeddium 0.3.31 BlockRenderer.writeGeometry before VBO encoding")
 private void rgbblocks$write(
      @Coerce Object context,@Coerce Object builder,Vec3 offset,@Coerce Object material,
      @Coerce Object quad,int[] colors,@Coerce Object lightData,CallbackInfo ci){
    try {
      if(quad==null || colors==null || lightData==null)return;
      if(rbQuadClass!=quad.getClass())rbResolveQuad(quad.getClass());
      if(rbLightClass!=lightData.getClass())rbResolveLight(lightData.getClass());
      int[] light=(int[])rbLightsField.get(lightData);
      for(int i=0;i<4;i++){
         float x=((Number)rbGetX.invoke(quad,i)).floatValue();
         float y=((Number)rbGetY.invoke(quad,i)).floatValue();
         float z=((Number)rbGetZ.invoke(quad,i)).floatValue();
         int oldLight=light[i],oldColor=colors[i];
         int updatedLight=SodiumRgbBridge.applyLight(oldLight,x,y,z,null);
         int updatedColor=SodiumRgbBridge.applyColorWithLight(oldColor,updatedLight,x,y,z,null);
         light[i]=updatedLight;
         colors[i]=updatedColor;
      }
    }catch(Throwable failure){rbReport(failure);}
 }
 @Unique private static void rbReport(Throwable failure){
    if(!rbReported){rbReported=true;System.err.println("RGBBlocks Embeddium 0.3.31 RGB bridge error: "+failure);}
 }
}
''',encoding="utf-8")
plugin=CODE/"com/rgbblocks/mixin/RGBBlocksMixinPlugin.java"
patch(plugin,lambda s:s.replace('mixinClassName.contains("Sodium")',
        '(mixinClassName.contains("Sodium") || mixinClassName.contains("Embeddium"))'))

# Minecraft Forge 1.20.1 requires mod root pack.mcmeta (resource pack format 15).
# Without this the entire 50,061-item model set can be absent at runtime even
# though it exists in the JAR; never claim texture/render parity until loaded.
(RES/"pack.mcmeta").write_text(json.dumps({"pack":{"pack_format":15,"description":"RGB Blocks 1.3.1 — Minecraft 1.20.1"}},ensure_ascii=False,indent=2),encoding="utf-8")

# Legacy Forge metadata; generated variant includes full data and old model schema.
modtoml=RES/"META-INF/mods.toml"
modtoml.parent.mkdir(parents=True,exist_ok=True)
modtoml.write_text('''modLoader="javafml"
loaderVersion="[47,)"
license="MIT"
[[mods]]
modId="rgbblocks"
version="1.3.1"
displayName="RGB Blocks"
description="RGB Blocks 1.3.1 backport to Minecraft 1.20.1"
[[dependencies.rgbblocks]]
modId="forge"
mandatory=true
versionRange="[47.4,)"
ordering="NONE"
side="BOTH"
[[dependencies.rgbblocks]]
modId="minecraft"
mandatory=true
versionRange="[1.20.1,1.20.2)"
ordering="NONE"
side="BOTH"
''',encoding="utf-8")
# Correct the mod description metadata only for loader compatibility;
# all palette names and original texture/language resources are retained.

(WORK/"settings.gradle").write_text('''pluginManagement {
  repositories {
    maven {url='https://maven.minecraftforge.net'}
    gradlePluginPortal()
    mavenCentral()
  }
}
rootProject.name='rgbblocks-mc1.20.1-forge'
''')
(WORK/"gradle.properties").write_text('''org.gradle.jvmargs=-Xmx4G
org.gradle.daemon=false
org.gradle.parallel=false
''')
(WORK/"build.gradle").write_text("""
buildscript {
 repositories { maven {url='https://repo.spongepowered.org/repository/maven-public'};mavenCentral() }
 dependencies { classpath 'org.spongepowered:mixingradle:0.7-SNAPSHOT' }
}
plugins { id 'net.minecraftforge.gradle' version '[6.0,6.2)' }
apply plugin: 'org.spongepowered.mixin'
group='com.rgbblocks'
version='1.3.1+mc1.20.1'
base { archivesName='RgbBlocksmod-MC1.20.1-Forge' }
java.toolchain.languageVersion=JavaLanguageVersion.of(17)
minecraft {
 mappings channel:'official',version:'1.20.1'
 copyIdeResources=true
 runs {
   client {
     workingDirectory project.file('run')
     property 'forge.logging.markers', 'REGISTRIES'
     property 'forge.logging.console.level', 'info'
     mods { rgbblocks {source sourceSets.main} }
   }
   server {
     workingDirectory project.file('run-server')
     property 'forge.logging.console.level', 'info'
     mods { rgbblocks {source sourceSets.main} }
   }
 }
}
repositories { maven {url='https://maven.minecraftforge.net'};mavenCentral() }
dependencies {
 minecraft 'net.minecraftforge:forge:1.20.1-47.4.28'
 annotationProcessor 'org.spongepowered:mixin:0.8.5:processor'
}
tasks.withType(JavaCompile).configureEach {options.release=17; options.encoding='UTF-8'}
tasks.withType(Zip).configureEach { zip64=true }
mixin {
  add sourceSets.main, 'rgbblocks.refmap.json'
  config 'rgbblocks.mixins.json'
}
jar.finalizedBy('reobfJar')
jar {
 manifest.attributes([
    'Specification-Title':'rgbblocks',
    'Specification-Vendor':'2bornot',
    'Specification-Version':'1',
    'Implementation-Title':project.name,
    'Implementation-Version':project.jar.archiveVersion,
    'Implementation-Vendor':'2bornot',
    'MixinConfigs':'rgbblocks.mixins.json'
 ])
}
""")
# Remove generated 1.21 Fabric mixin runtime metadata and patch original config
for file in RES.glob("*mixin*.json"):
    data=json.loads(file.read_text(encoding="utf-8"))
    data["compatibilityLevel"]="JAVA_17"
    data["refmap"]="rgbblocks.refmap.json"
    data.setdefault("client",[])
    data["client"]=[name for name in data["client"] if "Sodium06BlockRendererMixin" not in name]
    if "client.Embeddium03BlockRendererMixin" not in data["client"]:
       data["client"].append("client.Embeddium03BlockRendererMixin")
    file.write_text(json.dumps(data,indent=2),encoding="utf-8")
print("Forge 1.20.1 migration source staged: Java",len(list(CODE.rglob("*.java"))),
      "resources",len(list(RES.rglob("*"))),flush=True)
