package com.rgbblocks;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.rgbblocks.runtime.RGBRuntime;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.lang.reflect.Type;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Item.Properties;
import net.minecraft.world.level.ItemLike;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.StainedGlassBlock;
import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent.PlayerLoggedInEvent;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.DeferredRegister.Blocks;
import net.neoforged.neoforge.registries.DeferredRegister.Items;

@Mod("rgbblocks")
public class RgbBlocksMod {
   public static final String MODID = "rgbblocks";
   public static final Blocks BLOCKS = DeferredRegister.createBlocks("rgbblocks");
   public static final Items ITEMS = DeferredRegister.createItems("rgbblocks");
   public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, "rgbblocks");
   public static final List<DeferredItem<BlockItem>> NORMAL_ITEMS = new ArrayList<>();
   public static final List<DeferredItem<BlockItem>> GLOW_ITEMS = new ArrayList<>();
   public static final List<DeferredItem<BlockItem>> GLASS_ITEMS = new ArrayList<>();
   public static final DeferredItem<Item> RGB_LIGHT_SWITCH = ITEMS.register(
      "rgb_light_switch", () -> new RgbBlocksMod.RGBModeSwitchItem(itemProperties("rgb_light_switch"))
   );
   public static final DeferredItem<Item> RGB_LIGHT_BAKER = ITEMS.register(
      "rgb_light_baker", () -> new RgbBlocksMod.RGBLightBakerItem(itemProperties("rgb_light_baker"))
   );
   public static final DeferredHolder<CreativeModeTab, CreativeModeTab> NORMAL_TAB = TABS.register(
      "rgb_normal_tab",
      () -> CreativeModeTab.builder()
         .title(Component.literal("RGB Normal"))
         .icon(() -> new ItemStack(net.minecraft.world.item.Items.STONE))
         .displayItems((params, output) -> NORMAL_ITEMS.forEach(i -> output.accept((ItemLike)i.get())))
         .build()
   );
   public static final DeferredHolder<CreativeModeTab, CreativeModeTab> GLOW_TAB = TABS.register(
      "rgb_glow_tab",
      () -> CreativeModeTab.builder()
         .title(Component.literal("RGB Glow"))
         .icon(() -> new ItemStack(net.minecraft.world.item.Items.GLOWSTONE))
         .displayItems((params, output) -> GLOW_ITEMS.forEach(i -> output.accept((ItemLike)i.get())))
         .build()
   );
   public static final DeferredHolder<CreativeModeTab, CreativeModeTab> GLASS_TAB = TABS.register(
      "rgb_glass_tab",
      () -> CreativeModeTab.builder()
         .title(Component.literal("RGB Glass"))
         .icon(() -> new ItemStack(net.minecraft.world.item.Items.GLASS))
         .displayItems((params, output) -> GLASS_ITEMS.forEach(i -> output.accept((ItemLike)i.get())))
         .build()
   );
   public static final DeferredHolder<CreativeModeTab, CreativeModeTab> TOOLS_TAB = TABS.register(
      "rgb_tools_tab",
      () -> CreativeModeTab.builder()
         .title(Component.literal("RGB Tools"))
         .icon(() -> new ItemStack((ItemLike)RGB_LIGHT_SWITCH.get()))
         .displayItems((params, output) -> {
            output.accept((ItemLike)RGB_LIGHT_SWITCH.get());
            output.accept((ItemLike)RGB_LIGHT_BAKER.get());
         })
         .build()
   );

   public RgbBlocksMod(IEventBus modEventBus, ModContainer modContainer) {
      this.registerRGBBlocks();
      BLOCKS.register(modEventBus);
      ITEMS.register(modEventBus);
      TABS.register(modEventBus);
      modEventBus.addListener(this::registerPayloads);
      NeoForge.EVENT_BUS.addListener(this::registerCommands);
      NeoForge.EVENT_BUS.addListener(this::onPlayerLoggedIn);
   }

   private static Properties itemProperties(String name) {
      return new Properties().setId(ResourceKey.create(Registries.ITEM, Identifier.fromNamespaceAndPath("rgbblocks", name)));
   }

   private void registerPayloads(RegisterPayloadHandlersEvent event) {
      RGBRuntime.register(event.registrar("rgbblocks").versioned("1"));
   }

   private void onPlayerLoggedIn(PlayerLoggedInEvent event) {
      if (event.getEntity() instanceof ServerPlayer player) {
         RGBRuntime.sendState(player);
      }
   }

   private void registerCommands(RegisterCommandsEvent event) {
      event.getDispatcher()
         .register(
            (LiteralArgumentBuilder)((LiteralArgumentBuilder)((LiteralArgumentBuilder)((LiteralArgumentBuilder)((LiteralArgumentBuilder)((LiteralArgumentBuilder)Commands.literal(
                                 "rgb"
                              )
                              .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS)))
                           .then(Commands.literal("auto").executes(context -> {
                              RGBRuntime.setMode(((CommandSourceStack)context.getSource()).getServer(), RGBRuntime.Mode.AUTO);
                              ((CommandSourceStack)context.getSource()).sendSuccess(() -> Component.literal("RGB mode: AUTO"), true);
                              return 1;
                           })))
                        .then(Commands.literal("manual").executes(context -> {
                           RGBRuntime.setMode(((CommandSourceStack)context.getSource()).getServer(), RGBRuntime.Mode.MANUAL);
                           ((CommandSourceStack)context.getSource()).sendSuccess(() -> Component.literal("RGB mode: MANUAL"), true);
                           return 1;
                        })))
                     .then(
                        ((LiteralArgumentBuilder)Commands.literal("bake").executes(context -> {
                              RGBRuntime.RuntimeData data = RGBRuntime.data(((CommandSourceStack)context.getSource()).getServer());
                              RGBRuntime.broadcastBake(((CommandSourceStack)context.getSource()).getServer());
                              ((CommandSourceStack)context.getSource())
                                 .sendSuccess(() -> Component.literal("RGB bake requested (" + data.bakeDescription() + ")."), true);
                              return 1;
                           }))
                           .then(
                              Commands.literal("get")
                                 .executes(
                                    context -> sendRgbStatus(((CommandSourceStack)context.getSource()).getServer(), (CommandSourceStack)context.getSource())
                                 )
                           )
                     ))
                  .then(
                     Commands.literal("get")
                        .executes(context -> sendRgbStatus(((CommandSourceStack)context.getSource()).getServer(), (CommandSourceStack)context.getSource()))
                  ))
               .then(((LiteralArgumentBuilder)Commands.literal("setbake").then(Commands.literal("all").executes(context -> {
                  RGBRuntime.setBakeAll(((CommandSourceStack)context.getSource()).getServer());
                  ((CommandSourceStack)context.getSource()).sendSuccess(() -> Component.literal("RGB bake range: ALL dirty positions"), true);
                  return 1;
               }))).then(Commands.argument("radius", IntegerArgumentType.integer(4, 256)).executes(context -> {
                  int radius = IntegerArgumentType.getInteger(context, "radius");
                  RGBRuntime.setBakeRadius(((CommandSourceStack)context.getSource()).getServer(), radius);
                  ((CommandSourceStack)context.getSource()).sendSuccess(() -> Component.literal("RGB bake radius: " + radius), true);
                  return 1;
               })))
         );
   }

   private static int sendRgbStatus(MinecraftServer server, CommandSourceStack source) {
      RGBRuntime.RuntimeData data = RGBRuntime.data(server);
      String scope = data.bakeAll() ? "ALL" : "RADIUS " + data.bakeRadius();
      source.sendSuccess(() -> Component.literal("RGB mode: " + data.mode().name() + " | Bake scope: " + scope + " | World ID: " + data.worldId()), false);
      return 1;
   }

   private void registerRGBBlocks() {
      try {
         label110: {
            try (InputStream stream = RgbBlocksMod.class.getClassLoader().getResourceAsStream("assets/rgbblocks/palette.json")) {
               if (stream == null) {
                  System.out.println("palette.json not found.");
                  return;
               }

               try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
                  Gson gson = new Gson();
                  Type listType = (new TypeToken<List<RgbBlocksMod.ColorData>>() {}).getType();
                  List<RgbBlocksMod.ColorData> colors = (List<RgbBlocksMod.ColorData>)gson.fromJson(reader, listType);
                  if (colors != null && !colors.isEmpty()) {
                     System.out.println("Palette colors loaded: " + colors.size());

                     for (RgbBlocksMod.ColorData color : colors) {
                        String base = this.makeBaseName(color.group, color.red, color.green, color.blue);
                        DeferredBlock<Block> normal = BLOCKS.registerSimpleBlock(base, p -> p.mapColor(MapColor.STONE));
                        NORMAL_ITEMS.add(ITEMS.registerSimpleBlockItem(base, normal));
                        DeferredBlock<Block> glow = BLOCKS.registerSimpleBlock(base + "_glow", p -> p.mapColor(MapColor.STONE).lightLevel(s -> 15));
                        GLOW_ITEMS.add(ITEMS.registerSimpleBlockItem(base + "_glow", glow));
                        DeferredBlock<Block> glass = BLOCKS.registerBlock(
                           base + "_glass",
                           properties -> new StainedGlassBlock(
                              DyeColor.WHITE,
                              properties.mapColor(MapColor.NONE)
                                 .instrument(NoteBlockInstrument.HAT)
                                 .strength(0.3F)
                                 .sound(SoundType.GLASS)
                                 .noOcclusion()
                                 .isValidSpawn((s, g, p, ex) -> false)
                                 .isRedstoneConductor((s, g, p) -> false)
                                 .isSuffocating((s, g, p) -> false)
                                 .isViewBlocking((s, g, p) -> false)
                           )
                        );
                        GLASS_ITEMS.add(ITEMS.registerSimpleBlockItem(base + "_glass", glass));
                     }
                     break label110;
                  }

                  System.out.println("Palette is empty.");
               }
            }

            return;
         }
      } catch (Exception e) {
         System.out.println("Palette loading failed.");
         e.printStackTrace();
      }
   }

   private String makeBaseName(String group, int red, int green, int blue) {
      return "rgb_" + group + "_" + red + "_" + green + "_" + blue;
   }

   private static class ColorData {
      String group;
      int red;
      int green;
      int blue;
   }

   private static final class RGBLightBakerItem extends Item {
      private RGBLightBakerItem(Properties properties) {
         super(properties);
      }

      public InteractionResult use(Level level, Player player, InteractionHand hand) {
         if (level instanceof ServerLevel serverLevel) {
            RGBRuntime.RuntimeData data = RGBRuntime.data(serverLevel.getServer());
            RGBRuntime.broadcastBake(serverLevel.getServer());
            if (player instanceof ServerPlayer serverPlayer) {
               serverPlayer.sendSystemMessage(Component.literal("RGB bake requested (" + data.bakeDescription() + ")."), true);
            }

            return InteractionResult.SUCCESS_SERVER;
         } else {
            return InteractionResult.SUCCESS;
         }
      }
   }

   private static final class RGBModeSwitchItem extends Item {
      private RGBModeSwitchItem(Properties properties) {
         super(properties);
      }

      public InteractionResult use(Level level, Player player, InteractionHand hand) {
         if (level instanceof ServerLevel serverLevel) {
            RGBRuntime.Mode mode = RGBRuntime.toggleMode(serverLevel.getServer());
            if (player instanceof ServerPlayer serverPlayer) {
               serverPlayer.sendSystemMessage(Component.literal("RGB mode: " + mode.name()), true);
            }

            return InteractionResult.SUCCESS_SERVER;
         } else {
            return InteractionResult.SUCCESS;
         }
      }
   }
}
