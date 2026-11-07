package com.rgbblocks.runtime;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.UUID;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload.Type;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.datafix.DataFixTypes;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

public final class RGBRuntime {
   private static final int MIN_BAKE_RADIUS = 4;
   private static final int MAX_BAKE_RADIUS = 256;
   private static volatile RGBRuntime.Mode clientTargetMode = RGBRuntime.Mode.AUTO;
   private static volatile boolean clientBakeAll;
   private static volatile int clientBakeRadius = 32;
   private static volatile RGBRuntime.BakeRequest pendingBakeRequest;
   private static volatile boolean clientBootstrapAllowed = true;
   private static volatile long clientStateVersion;
   private static volatile String clientWorldId = "";

   private RGBRuntime() {
   }

   public static RGBRuntime.Mode clientTargetMode() {
      return clientTargetMode;
   }

   public static boolean clientTargetAuto() {
      return clientTargetMode == RGBRuntime.Mode.AUTO;
   }

   public static boolean clientTargetManual() {
      return clientTargetMode == RGBRuntime.Mode.MANUAL;
   }

   public static boolean clientBakeAll() {
      return clientBakeAll;
   }

   public static int clientBakeRadius() {
      return clientBakeRadius;
   }

   public static long clientStateVersion() {
      return clientStateVersion;
   }

   public static String clientWorldId() {
      return clientWorldId;
   }

   public static boolean clientBootstrapAllowed() {
      return clientBootstrapAllowed;
   }

   public static void setClientBootstrapAllowed(boolean allowed) {
      clientBootstrapAllowed = allowed;
   }

   public static RGBRuntime.BakeRequest consumeBakeRequest() {
      RGBRuntime.BakeRequest request = pendingBakeRequest;
      pendingBakeRequest = null;
      return request;
   }

   public static void resetClientState() {
      clientTargetMode = RGBRuntime.Mode.AUTO;
      clientBakeAll = false;
      clientBakeRadius = 32;
      pendingBakeRequest = null;
      clientBootstrapAllowed = true;
      clientWorldId = "";
      clientStateVersion++;
   }

   public static RGBRuntime.RuntimeData data(MinecraftServer server) {
      return (RGBRuntime.RuntimeData)server.getDataStorage().computeIfAbsent(RGBRuntime.RuntimeData.TYPE);
   }

   public static void setMode(MinecraftServer server, RGBRuntime.Mode mode) {
      RGBRuntime.RuntimeData data = data(server);
      data.setMode(mode);
      broadcastState(server);
   }

   public static RGBRuntime.Mode toggleMode(MinecraftServer server) {
      RGBRuntime.RuntimeData data = data(server);
      RGBRuntime.Mode next = data.mode() == RGBRuntime.Mode.AUTO ? RGBRuntime.Mode.MANUAL : RGBRuntime.Mode.AUTO;
      data.setMode(next);
      broadcastState(server);
      return next;
   }

   public static void setBakeAll(MinecraftServer server) {
      RGBRuntime.RuntimeData data = data(server);
      data.setBakeAll();
      broadcastState(server);
   }

   public static void setBakeRadius(MinecraftServer server, int radius) {
      RGBRuntime.RuntimeData data = data(server);
      data.setBakeRadius(radius);
      broadcastState(server);
   }

   public static void registerPayloadTypes() {
      PayloadTypeRegistry.clientboundPlay().register(RGBRuntime.StatePayload.TYPE, RGBRuntime.StatePayload.STREAM_CODEC);
      PayloadTypeRegistry.clientboundPlay().register(RGBRuntime.BakePayload.TYPE, RGBRuntime.BakePayload.STREAM_CODEC);
   }

   public static void sendState(ServerPlayer player) {
      MinecraftServer server = player.level().getServer();
      if (server != null && ServerPlayNetworking.canSend(player, RGBRuntime.StatePayload.TYPE)) {
         RGBRuntime.RuntimeData data = data(server);
         ServerPlayNetworking.send(player, new RGBRuntime.StatePayload(data.mode() == RGBRuntime.Mode.AUTO, data.bakeAll(), data.bakeRadius(), data.worldId()));
      }
   }

   public static void broadcastState(MinecraftServer server) {
      RGBRuntime.RuntimeData data = data(server);
      RGBRuntime.StatePayload payload = new RGBRuntime.StatePayload(data.mode() == RGBRuntime.Mode.AUTO, data.bakeAll(), data.bakeRadius(), data.worldId());

      for (ServerPlayer player : server.getPlayerList().getPlayers()) {
         if (ServerPlayNetworking.canSend(player, RGBRuntime.StatePayload.TYPE)) {
            ServerPlayNetworking.send(player, payload);
         }
      }
   }

   public static void broadcastBake(MinecraftServer server) {
      RGBRuntime.RuntimeData data = data(server);
      RGBRuntime.BakePayload payload = new RGBRuntime.BakePayload(data.bakeAll(), data.bakeRadius());

      for (ServerPlayer player : server.getPlayerList().getPlayers()) {
         if (ServerPlayNetworking.canSend(player, RGBRuntime.BakePayload.TYPE)) {
            ServerPlayNetworking.send(player, payload);
         }
      }
   }

   public static void acceptState(RGBRuntime.StatePayload payload) {
      clientTargetMode = payload.auto ? RGBRuntime.Mode.AUTO : RGBRuntime.Mode.MANUAL;
      clientBakeAll = payload.bakeAll;
      clientBakeRadius = clamp(payload.bakeRadius, 4, 256);
      clientWorldId = payload.worldId == null ? "" : payload.worldId;
      clientStateVersion++;
   }

   public static void acceptBake(RGBRuntime.BakePayload payload) {
      clientBakeAll = payload.all;
      clientBakeRadius = clamp(payload.radius, 4, 256);
      pendingBakeRequest = new RGBRuntime.BakeRequest(payload.all, clientBakeRadius);
   }

   private static int clamp(int value, int min, int max) {
      return value < min ? min : Math.min(value, max);
   }

   public record BakePayload(boolean all, int radius) implements CustomPacketPayload {
      public static final Type<RGBRuntime.BakePayload> TYPE = new Type(Identifier.fromNamespaceAndPath("rgbblocks", "bake"));
      public static final StreamCodec<FriendlyByteBuf, RGBRuntime.BakePayload> STREAM_CODEC = StreamCodec.of((buf, payload) -> {
         buf.writeBoolean(payload.all);
         buf.writeInt(payload.radius);
      }, buf -> new RGBRuntime.BakePayload(buf.readBoolean(), buf.readInt()));

      public Type<? extends CustomPacketPayload> type() {
         return TYPE;
      }
   }

   public record BakeRequest(boolean all, int radius) {
   }

   public enum Mode {
      AUTO,
      MANUAL;
   }

   public static final class RuntimeData extends SavedData {
      private static final Codec<RGBRuntime.RuntimeData> CODEC = RecordCodecBuilder.create(
         instance -> instance.group(
               Codec.STRING.optionalFieldOf("mode", RGBRuntime.Mode.AUTO.name()).forGetter(data -> data.mode.name()),
               Codec.BOOL.optionalFieldOf("bake_all", false).forGetter(RGBRuntime.RuntimeData::bakeAll),
               Codec.INT.optionalFieldOf("bake_radius", 32).forGetter(RGBRuntime.RuntimeData::bakeRadius),
               Codec.STRING.optionalFieldOf("world_id", "").forGetter(RGBRuntime.RuntimeData::worldId)
            )
            .apply(instance, RGBRuntime.RuntimeData::new)
      );
      public static final SavedDataType<RGBRuntime.RuntimeData> TYPE = new SavedDataType(
         Identifier.fromNamespaceAndPath("rgbblocks", "runtime"), RGBRuntime.RuntimeData::new, CODEC, DataFixTypes.SAVED_DATA_COMMAND_STORAGE
      );
      private RGBRuntime.Mode mode;
      private boolean bakeAll;
      private int bakeRadius;
      private String worldId;

      public RuntimeData() {
         this(RGBRuntime.Mode.AUTO.name(), false, 32, UUID.randomUUID().toString());
      }

      private RuntimeData(String mode, boolean bakeAll, int bakeRadius, String worldId) {
         try {
            this.mode = RGBRuntime.Mode.valueOf(mode);
         } catch (IllegalArgumentException ignored) {
            this.mode = RGBRuntime.Mode.AUTO;
         }

         this.bakeAll = bakeAll;
         this.bakeRadius = RGBRuntime.clamp(bakeRadius, 4, 256);
         if (worldId != null && !worldId.isBlank()) {
            this.worldId = worldId;
         } else {
            this.worldId = UUID.randomUUID().toString();
            this.setDirty();
         }
      }

      public RGBRuntime.Mode mode() {
         return this.mode;
      }

      public boolean bakeAll() {
         return this.bakeAll;
      }

      public int bakeRadius() {
         return this.bakeRadius;
      }

      public String worldId() {
         return this.worldId;
      }

      public String bakeDescription() {
         return this.bakeAll ? "ALL dirty positions" : "radius " + this.bakeRadius;
      }

      public void setMode(RGBRuntime.Mode mode) {
         RGBRuntime.Mode next = mode == null ? RGBRuntime.Mode.AUTO : mode;
         if (this.mode != next) {
            this.mode = next;
            this.setDirty();
         }
      }

      public void setBakeAll() {
         if (!this.bakeAll) {
            this.bakeAll = true;
            this.setDirty();
         }
      }

      public void setBakeRadius(int radius) {
         int next = RGBRuntime.clamp(radius, 4, 256);
         if (this.bakeAll || this.bakeRadius != next) {
            this.bakeAll = false;
            this.bakeRadius = next;
            this.setDirty();
         }
      }
   }

   public record StatePayload(boolean auto, boolean bakeAll, int bakeRadius, String worldId) implements CustomPacketPayload {
      public static final Type<RGBRuntime.StatePayload> TYPE = new Type(Identifier.fromNamespaceAndPath("rgbblocks", "runtime_state"));
      public static final StreamCodec<FriendlyByteBuf, RGBRuntime.StatePayload> STREAM_CODEC = StreamCodec.of((buf, payload) -> {
         buf.writeBoolean(payload.auto);
         buf.writeBoolean(payload.bakeAll);
         buf.writeInt(payload.bakeRadius);
         buf.writeUtf(payload.worldId == null ? "" : payload.worldId);
      }, buf -> new RGBRuntime.StatePayload(buf.readBoolean(), buf.readBoolean(), buf.readInt(), buf.readUtf()));

      public Type<? extends CustomPacketPayload> type() {
         return TYPE;
      }
   }
}
