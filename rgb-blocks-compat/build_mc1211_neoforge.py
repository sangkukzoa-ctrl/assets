#!/usr/bin/env python3
"""RGB Blocks 1.3.1 -> Minecraft 1.21.1 NeoForge.
Port from the original NeoForge 26.1.2 class/layout contract while keeping
the already migrated 1.21.1 Minecraft lighting/microblock code and identical
original palette, IDs and textures. This is a BUILD CANDIDATE, not a release.
"""
from pathlib import Path
import shutil,json,re

ROOT=Path("port-work/mc1211-neoforge")
BASE=Path("port-work/mc1211-fabric")
if not BASE.exists():
    raise RuntimeError("First generate the common Minecraft 1.21.1 compatibility source with build_mc1211_fabric.py")
shutil.rmtree(ROOT,ignore_errors=True)
shutil.copytree(BASE/"src",ROOT/"src")
JAVA=ROOT/"src/main/java/com/rgbblocks"
RES=ROOT/"src/main/resources"
(RES/"fabric.mod.json").unlink(missing_ok=True)
# The original 1.3.1 NeoForge mod's structure is preserved: RgbBlocksMod,
# RGBRuntime, lighting/cnb/render classes, mixin plugin and original resources.

(JAVA/"RgbBlocksMod.java").write_text('''package com.rgbblocks;
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
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.*;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.*;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.*;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.registries.*;

@Mod(RgbBlocksMod.MODID)
public final class RgbBlocksMod {
 public static final String MODID="rgbblocks";
 public static final DeferredRegister.Blocks BLOCKS=DeferredRegister.createBlocks(MODID);
 public static final DeferredRegister.Items ITEMS=DeferredRegister.createItems(MODID);
 public static final DeferredRegister<CreativeModeTab> TABS=DeferredRegister.create(Registries.CREATIVE_MODE_TAB,MODID);
 public static final List<DeferredItem<BlockItem>> NORMAL_ITEMS=new ArrayList<>();
 public static final List<DeferredItem<BlockItem>> GLOW_ITEMS=new ArrayList<>();
 public static final List<DeferredItem<BlockItem>> GLASS_ITEMS=new ArrayList<>();
 public static final DeferredItem<Item> RGB_LIGHT_SWITCH=ITEMS.register("rgb_light_switch",()->new RGBModeSwitchItem(new Item.Properties()));
 public static final DeferredItem<Item> RGB_LIGHT_BAKER=ITEMS.register("rgb_light_baker",()->new RGBLightBakerItem(new Item.Properties()));
 public static final DeferredHolder<CreativeModeTab,CreativeModeTab> NORMAL_TAB=TABS.register("rgb_normal_tab",
   ()->CreativeModeTab.builder().title(Component.literal("RGB Normal"))
     .icon(()->new ItemStack(net.minecraft.world.item.Items.STONE))
     .displayItems((params,out)->NORMAL_ITEMS.forEach(i->out.accept(i.get()))).build());
 public static final DeferredHolder<CreativeModeTab,CreativeModeTab> GLOW_TAB=TABS.register("rgb_glow_tab",
   ()->CreativeModeTab.builder().title(Component.literal("RGB Glow"))
     .icon(()->new ItemStack(net.minecraft.world.item.Items.GLOWSTONE))
     .displayItems((params,out)->GLOW_ITEMS.forEach(i->out.accept(i.get()))).build());
 public static final DeferredHolder<CreativeModeTab,CreativeModeTab> GLASS_TAB=TABS.register("rgb_glass_tab",
   ()->CreativeModeTab.builder().title(Component.literal("RGB Glass"))
     .icon(()->new ItemStack(net.minecraft.world.item.Items.GLASS))
     .displayItems((params,out)->GLASS_ITEMS.forEach(i->out.accept(i.get()))).build());
 public static final DeferredHolder<CreativeModeTab,CreativeModeTab> TOOLS_TAB=TABS.register("rgb_tools_tab",
   ()->CreativeModeTab.builder().title(Component.literal("RGB Tools"))
     .icon(()->new ItemStack(RGB_LIGHT_SWITCH.get()))
     .displayItems((params,out)->{out.accept(RGB_LIGHT_SWITCH.get());out.accept(RGB_LIGHT_BAKER.get());}).build());

 public RgbBlocksMod(IEventBus modBus,ModContainer container){
   int colors=registerRGBBlocks();
   BLOCKS.register(modBus); ITEMS.register(modBus); TABS.register(modBus);
   modBus.addListener(this::registerPayloads);
   NeoForge.EVENT_BUS.addListener(this::registerCommands);
   NeoForge.EVENT_BUS.addListener(this::onLogin);
   System.out.println("RGB Blocks 1.3.1 NeoForge 1.21.1 palette "+colors+" colors / "+(colors*3)+" RGB blocks");
 }
 private void registerPayloads(RegisterPayloadHandlersEvent event){
   RGBRuntime.register(event.registrar("1"));
 }
 private void onLogin(PlayerEvent.PlayerLoggedInEvent event){
   if(event.getEntity() instanceof ServerPlayer p)RGBRuntime.sendState(p);
 }
 private static int registerRGBBlocks(){
   try(InputStream is=RgbBlocksMod.class.getClassLoader().getResourceAsStream("assets/rgbblocks/palette.json")){
     if(is==null)throw new IllegalStateException("Missing original 1.3.1 palette.json");
     try(Reader reader=new InputStreamReader(is,StandardCharsets.UTF_8)){
       Type type=new TypeToken<List<ColorData>>(){}.getType();
       List<ColorData> colors=new Gson().fromJson(reader,type);
       if(colors==null || colors.size()!=16687)throw new IllegalStateException("Palette parity violation "+(colors==null?0:colors.size()));
       for(ColorData c:colors){
         String name="rgb_"+c.group+"_"+c.red+"_"+c.green+"_"+c.blue;
         DeferredBlock<Block> n=BLOCKS.registerSimpleBlock(name,BlockBehaviour.Properties.of().mapColor(MapColor.STONE));
         NORMAL_ITEMS.add(ITEMS.registerSimpleBlockItem(name,n));
         DeferredBlock<Block> g=BLOCKS.registerSimpleBlock(name+"_glow",BlockBehaviour.Properties.of().mapColor(MapColor.STONE).lightLevel(s->15));
         GLOW_ITEMS.add(ITEMS.registerSimpleBlockItem(name+"_glow",g));
         DeferredBlock<StainedGlassBlock> glass=BLOCKS.registerBlock(name+"_glass",
          props->new StainedGlassBlock(DyeColor.WHITE,props.mapColor(MapColor.NONE)
           .instrument(NoteBlockInstrument.HAT).strength(0.3f).sound(SoundType.GLASS).noOcclusion()
           .isValidSpawn((s,w,p,e)->false)
           .isRedstoneConductor((s,w,p)->false)
           .isSuffocating((s,w,p)->false)
           .isViewBlocking((s,w,p)->false)),
          BlockBehaviour.Properties.of());
         GLASS_ITEMS.add(ITEMS.registerSimpleBlockItem(name+"_glass",glass));
       }
       return colors.size();
     }
   }catch(IOException ex){throw new IllegalStateException("Original RGB palette registration failed",ex);}
 }
 private static final class ColorData{String group;int red,green,blue;}
 private void registerCommands(RegisterCommandsEvent e){registerCommands(e.getDispatcher());}
 private static void registerCommands(CommandDispatcher<CommandSourceStack> d){
   d.register(Commands.literal("rgb").requires(src->src.hasPermission(2))
      .then(Commands.literal("auto").executes(c->{
        RGBRuntime.setMode(c.getSource().getServer(),RGBRuntime.Mode.AUTO);
        c.getSource().sendSuccess(()->Component.literal("RGB mode: AUTO"),true);return 1;}))
      .then(Commands.literal("manual").executes(c->{
        RGBRuntime.setMode(c.getSource().getServer(),RGBRuntime.Mode.MANUAL);
        c.getSource().sendSuccess(()->Component.literal("RGB mode: MANUAL"),true);return 1;}))
      .then(Commands.literal("bake").executes(c->{
        var data=RGBRuntime.data(c.getSource().getServer());RGBRuntime.broadcastBake(c.getSource().getServer());
        c.getSource().sendSuccess(()->Component.literal("RGB bake requested ("+data.bakeDescription()+")."),true);return 1;}))
      .then(Commands.literal("get").executes(c->status(c.getSource().getServer(),c.getSource())))
      .then(Commands.literal("setbake")
       .then(Commands.literal("all").executes(c->{
          RGBRuntime.setBakeAll(c.getSource().getServer());
          c.getSource().sendSuccess(()->Component.literal("RGB bake range: ALL dirty positions"),true);return 1;}))
       .then(Commands.argument("radius",IntegerArgumentType.integer(4,256)).executes(c->{
          int radius=IntegerArgumentType.getInteger(c,"radius");
          RGBRuntime.setBakeRadius(c.getSource().getServer(),radius);
          c.getSource().sendSuccess(()->Component.literal("RGB bake radius: "+radius),true);return 1;}))));
 }
 private static int status(MinecraftServer server,CommandSourceStack source){
   var d=RGBRuntime.data(server);
   source.sendSuccess(()->Component.literal("RGB mode: "+d.mode().name()+" | Bake scope: "+
       (d.bakeAll()?"ALL":"RADIUS "+d.bakeRadius())+" | World ID: "+d.worldId()),false);
   return 1;
 }
 private static final class RGBModeSwitchItem extends Item{
   private RGBModeSwitchItem(Properties p){super(p);}
   @Override public InteractionResultHolder<ItemStack> use(Level level,Player player,InteractionHand hand){
      if(level instanceof ServerLevel serverLevel){
        var mode=RGBRuntime.toggleMode(serverLevel.getServer());
        if(player instanceof ServerPlayer sp)sp.sendSystemMessage(Component.literal("RGB mode: "+mode.name()),true);
      }
      return InteractionResultHolder.sidedSuccess(player.getItemInHand(hand),level.isClientSide);
   }
 }
 private static final class RGBLightBakerItem extends Item{
   private RGBLightBakerItem(Properties p){super(p);}
   @Override public InteractionResultHolder<ItemStack> use(Level level,Player player,InteractionHand hand){
      if(level instanceof ServerLevel serverLevel){
        var data=RGBRuntime.data(serverLevel.getServer());
        RGBRuntime.broadcastBake(serverLevel.getServer());
        if(player instanceof ServerPlayer sp)sp.sendSystemMessage(Component.literal("RGB bake requested ("+data.bakeDescription()+")."),true);
      }
      return InteractionResultHolder.sidedSuccess(player.getItemInHand(hand),level.isClientSide);
   }
 }
}
''',encoding="utf-8")

rt=JAVA/"runtime/RGBRuntime.java"
s=rt.read_text(encoding="utf-8")
s=s.replace('import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;',
 '''import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.network.handling.IPayloadContext;
import net.neoforged.neoforge.network.registration.PayloadRegistrar;''')
s=s.replace('import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;','')
a=s.index("   public static void registerPayloadTypes()")
b=s.index("   public static void acceptState(",a)
s=s[:a]+'''   public static void register(PayloadRegistrar registrar){
     registrar.playToClient(StatePayload.TYPE,StatePayload.STREAM_CODEC,(msg,ctx)->ctx.enqueueWork(()->acceptState(msg)));
     registrar.playToClient(BakePayload.TYPE,BakePayload.STREAM_CODEC,(msg,ctx)->ctx.enqueueWork(()->acceptBake(msg)));
   }
   public static void sendState(ServerPlayer player){
     MinecraftServer server=player.level().getServer();
     if(server!=null){
       var d=data(server);
       PacketDistributor.sendToPlayer(player,new StatePayload(d.mode()==Mode.AUTO,d.bakeAll(),d.bakeRadius(),d.worldId()));
     }
   }
   public static void broadcastState(MinecraftServer server){
      var d=data(server);
      PacketDistributor.sendToAllPlayers(new StatePayload(d.mode()==Mode.AUTO,d.bakeAll(),d.bakeRadius(),d.worldId()));
   }
   public static void broadcastBake(MinecraftServer server){
      var d=data(server);
      PacketDistributor.sendToAllPlayers(new BakePayload(d.bakeAll(),d.bakeRadius()));
   }
'''+s[b:]
rt.write_text(s,encoding="utf-8")

# Keep settings, renderer, and light engine class locations identical.
config=JAVA/"client/config/RGBClientConfig.java"
s=config.read_text(encoding="utf-8").replace("net.fabricmc.loader.api.FabricLoader","net.neoforged.fml.loading.FMLPaths")
s=s.replace("FabricLoader.getInstance().getConfigDir()","FMLPaths.CONFIGDIR.get()")
config.write_text(s,encoding="utf-8")

# Restore the ORIGINAL 1.3.1 NeoForge Mixin plugin, not the Fabric loader's
# optional-mixin discovery implementation. Preserve platform source structure.
plugin=JAVA/"mixin/RGBBlocksMixinPlugin.java"
original_plugin=Path("rgb-blocks-compat/recovered/neoforge/com/rgbblocks/mixin/RGBBlocksMixinPlugin.java")
shutil.copy2(original_plugin,plugin)

client=JAVA/"client/RgbBlocksClient.java"
client.write_text('''package com.rgbblocks.client;
import com.rgbblocks.client.config.RGBClientConfig;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
@EventBusSubscriber(modid="rgbblocks",bus=EventBusSubscriber.Bus.MOD,value=Dist.CLIENT)
public final class RgbBlocksClient {
 private RgbBlocksClient(){}
 @SubscribeEvent public static void clientSetup(FMLClientSetupEvent event){
    event.enqueueWork(RGBClientConfig::initialize);
 }
}
''',encoding="utf-8")

# 26.1.2 to 1.21.1 resource codec conversion was done in the shared stage,
# but any Fabric-only mods must be absent in this NeoForge deliverable.
leftovers=[]
for p in JAVA.rglob("*.java"):
    s=p.read_text(encoding="utf-8")
    if "net.fabricmc" in s or "FabricLoader" in s or "ServerPlayNetworking" in s:
        leftovers.append(str(p.relative_to(JAVA)))
assert not leftovers,("Fabric-only classes leaked into NeoForge:",leftovers)

toml=RES/"META-INF/neoforge.mods.toml";toml.parent.mkdir(parents=True,exist_ok=True)
toml.write_text('''modLoader="javafml"
loaderVersion="[1,)"
license="All Rights Reserved"
[[mods]]
modId="rgbblocks"
version="1.3.1+mc1.21.1"
displayName="RGB Blocks"
description="Original RGB Blocks 1.3.1 functionality ported to Minecraft 1.21.1 NeoForge."
[[dependencies.rgbblocks]]
modId="neoforge"
type="required"
versionRange="[21.1.218,)"
ordering="NONE"
side="BOTH"
[[dependencies.rgbblocks]]
modId="minecraft"
type="required"
versionRange="[1.21.1,1.21.2)"
ordering="NONE"
side="BOTH"
''',encoding="utf-8")
for file in RES.glob("*mixins*.json"):
    obj=json.loads(file.read_text(encoding="utf-8"))
    obj["compatibilityLevel"]="JAVA_21"
    file.write_text(json.dumps(obj,indent=2),encoding="utf-8")
    with toml.open("a",encoding="utf-8") as o:o.write('\\n[[mixins]]\\nconfig="'+file.name+'"\\n')

(ROOT/"settings.gradle").write_text('''pluginManagement { repositories { gradlePluginPortal(); mavenCentral() } }
rootProject.name="rgbblocks-1.21.1-neoforge"
''',encoding="utf-8")
(ROOT/"gradle.properties").write_text('''org.gradle.jvmargs=-Xmx4G
org.gradle.daemon=false
org.gradle.parallel=false
org.gradle.caching=true
''',encoding="utf-8")
(ROOT/"build.gradle").write_text('''plugins {
    id 'java-library'
    id 'net.neoforged.moddev' version '2.0.148'
}
group='com.rgbblocks'
version='1.3.1+mc1.21.1'
base { archivesName='RgbBlocksmod-MC1.21.1-NeoForge' }
java.toolchain.languageVersion=JavaLanguageVersion.of(21)
neoForge { version='21.1.265' }
tasks.withType(JavaCompile).configureEach {options.encoding='UTF-8';options.release=21}
tasks.withType(Zip).configureEach {zip64=true}
''',encoding="utf-8")
print("NEOFORGE 1.21.1 PORT STAGED:",len(list(JAVA.rglob("*.java"))),"Java classes",
 len(list(RES.rglob("*"))),"resource entries",flush=True)
