package com.rgbblocks;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import com.mojang.brigadier.CommandDispatcher;
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
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents.Join;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
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
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.StainedGlassBlock;
import net.minecraft.world.level.block.state.BlockBehaviour.Properties;
import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;
import net.minecraft.world.level.material.MapColor;

public final class RgbBlocksMod implements ModInitializer {
   public static final String MODID = "rgbblocks";
   public static final List<Item> NORMAL_ITEMS = new ArrayList<>();
   public static final List<Item> GLOW_ITEMS = new ArrayList<>();
   public static final List<Item> GLASS_ITEMS = new ArrayList<>();
   public static Item RGB_LIGHT_SWITCH;
   public static Item RGB_LIGHT_BAKER;

   public void onInitialize() {
      int paletteSize = registerRGBBlocks();
      RGB_LIGHT_SWITCH = registerItem("rgb_light_switch", RgbBlocksMod.RGBModeSwitchItem::new);
      RGB_LIGHT_BAKER = registerItem("rgb_light_baker", RgbBlocksMod.RGBLightBakerItem::new);
      registerCreativeTabs();
      RGBRuntime.registerPayloadTypes();
      CommandRegistrationCallback.EVENT.register((CommandRegistrationCallback)(dispatcher, buildContext, selection) -> registerCommands(dispatcher));
      ServerPlayConnectionEvents.JOIN.register((Join)(handler, sender, server) -> RGBRuntime.sendState(handler.player));
      System.out.println("RGB Blocks Fabric loaded: " + paletteSize + " palette colors / " + paletteSize * 3 + " blocks registered.");
   }

   private static Identifier id(String path) {
      return Identifier.fromNamespaceAndPath("rgbblocks", path);
   }

   private static ResourceKey<Block> blockKey(String path) {
      return ResourceKey.create(Registries.BLOCK, id(path));
   }

   private static ResourceKey<Item> itemKey(String path) {
      return ResourceKey.create(Registries.ITEM, id(path));
   }

   private static Block registerBlock(String path, RgbBlocksMod.BlockFactory factory) {
      ResourceKey<Block> key = blockKey(path);
      Block block = factory.create(Properties.of().setId(key));
      Registry.register(BuiltInRegistries.BLOCK, key, block);
      ResourceKey<Item> blockItemKey = itemKey(path);
      Item blockItem = new BlockItem(block, new net.minecraft.world.item.Item.Properties().setId(blockItemKey).useBlockDescriptionPrefix());
      Registry.register(BuiltInRegistries.ITEM, blockItemKey, blockItem);
      return block;
   }

   private static Item registerItem(String path, RgbBlocksMod.ItemFactory factory) {
      ResourceKey<Item> key = itemKey(path);
      Item item = factory.create(new net.minecraft.world.item.Item.Properties().setId(key));
      return (Item)Registry.register(BuiltInRegistries.ITEM, key, item);
   }

   private static void registerCreativeTabs() {
      registerTab(
         "rgb_normal_tab",
         FabricCreativeModeTab.builder()
            .title(Component.literal("RGB Normal"))
            .icon(() -> new ItemStack(Items.STONE))
            .displayItems((params, output) -> NORMAL_ITEMS.forEach(output::accept))
            .build()
      );
      registerTab(
         "rgb_glow_tab",
         FabricCreativeModeTab.builder()
            .title(Component.literal("RGB Glow"))
            .icon(() -> new ItemStack(Items.GLOWSTONE))
            .displayItems((params, output) -> GLOW_ITEMS.forEach(output::accept))
            .build()
      );
      registerTab(
         "rgb_glass_tab",
         FabricCreativeModeTab.builder()
            .title(Component.literal("RGB Glass"))
            .icon(() -> new ItemStack(Items.GLASS))
            .displayItems((params, output) -> GLASS_ITEMS.forEach(output::accept))
            .build()
      );
      registerTab(
         "rgb_tools_tab",
         FabricCreativeModeTab.builder().title(Component.literal("RGB Tools")).icon(() -> new ItemStack(RGB_LIGHT_SWITCH)).displayItems((params, output) -> {
            output.accept(RGB_LIGHT_SWITCH);
            output.accept(RGB_LIGHT_BAKER);
         }).build()
      );
   }

   private static CreativeModeTab registerTab(String path, CreativeModeTab tab) {
      ResourceKey<CreativeModeTab> key = ResourceKey.create(Registries.CREATIVE_MODE_TAB, id(path));
      return (CreativeModeTab)Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, key, tab);
   }

   private static void registerCommands(CommandDispatcher<CommandSourceStack> dispatcher) {
      dispatcher.register(
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

   private static int registerRGBBlocks() {
      try (InputStream stream = RgbBlocksMod.class.getClassLoader().getResourceAsStream("assets/rgbblocks/palette.json")) {
         if (stream == null) {
            System.err.println("RGB Blocks palette.json not found.");
            return 0;
         }

         try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            Gson gson = new Gson();
            Type listType = (new TypeToken<List<RgbBlocksMod.ColorData>>() {}).getType();
            List<RgbBlocksMod.ColorData> colors = (List<RgbBlocksMod.ColorData>)gson.fromJson(reader, listType);
            if (colors == null || colors.isEmpty()) {
               System.err.println("RGB Blocks palette is empty.");
               return 0;
            }

            for (RgbBlocksMod.ColorData color : colors) {
               String base = makeBaseName(color.group, color.red, color.green, color.blue);
               Block normal = registerBlock(base, properties -> new Block(properties.mapColor(MapColor.STONE)));
               NORMAL_ITEMS.add(normal.asItem());
               Block glow = registerBlock(base + "_glow", properties -> new Block(properties.mapColor(MapColor.STONE).lightLevel(state -> 15)));
               GLOW_ITEMS.add(glow.asItem());
               Block glass = registerBlock(
                  base + "_glass",
                  properties -> new StainedGlassBlock(
                     DyeColor.WHITE,
                     properties.mapColor(MapColor.NONE)
                        .instrument(NoteBlockInstrument.HAT)
                        .strength(0.3F)
                        .sound(SoundType.GLASS)
                        .noOcclusion()
                        .isValidSpawn((state, level, pos, entityType) -> false)
                        .isRedstoneConductor((state, level, pos) -> false)
                        .isSuffocating((state, level, pos) -> false)
                        .isViewBlocking((state, level, pos) -> false)
                  )
               );
               GLASS_ITEMS.add(glass.asItem());
            }

            return colors.size();
         }
      } catch (Exception exception) {
         throw new IllegalStateException("RGB Blocks palette registration failed", exception);
      }
   }

   private static String makeBaseName(String group, int red, int green, int blue) {
      return "rgb_" + group + "_" + red + "_" + green + "_" + blue;
   }

   @FunctionalInterface
   private interface BlockFactory {
      Block create(Properties var1);
   }

   private static final class ColorData {
      String group;
      int red;
      int green;
      int blue;
   }

   @FunctionalInterface
   private interface ItemFactory {
      Item create(net.minecraft.world.item.Item.Properties var1);
   }

   private static final class RGBLightBakerItem extends Item {
      private RGBLightBakerItem(net.minecraft.world.item.Item.Properties properties) {
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
      private RGBModeSwitchItem(net.minecraft.world.item.Item.Properties properties) {
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
