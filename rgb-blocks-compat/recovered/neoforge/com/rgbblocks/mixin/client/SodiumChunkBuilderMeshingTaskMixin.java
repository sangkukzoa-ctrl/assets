package com.rgbblocks.mixin.client;

import com.rgbblocks.client.lighting.SodiumRgbBridge;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.block.BlockAndTintGetter;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Dynamic;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Redirect;

@Pseudo
@Mixin(targets = "net.caffeinemc.mods.sodium.client.render.chunk.compile.tasks.ChunkBuilderMeshingTask", remap = false)
public abstract class SodiumChunkBuilderMeshingTaskMixin {
   @Redirect(
      method = "execute(Lnet/caffeinemc/mods/sodium/client/render/chunk/compile/ChunkBuildContext;Lnet/caffeinemc/mods/sodium/client/util/task/CancellationToken;)Lnet/caffeinemc/mods/sodium/client/render/chunk/compile/ChunkBuildOutput;",
      at = @At(
         value = "INVOKE",
         target = "Lnet/caffeinemc/mods/sodium/client/render/chunk/compile/pipeline/BlockRenderer;renderModel(Lnet/minecraft/client/renderer/block/dispatch/BlockStateModel;Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/core/BlockPos;Lnet/minecraft/core/BlockPos;)V",
         remap = false
      ),
      require = 0,
      remap = false
   )
   @Dynamic("Sodium 0.8.x internal chunk meshing pipeline")
   private void rgbblocks$renderModelWithRgbContext(@Coerce Object blockRenderer, @Coerce Object model, BlockState state, BlockPos pos, BlockPos origin) {
      Object level = readField(blockRenderer, "level");
      if (!(level instanceof BlockAndTintGetter)) {
         try {
            level = Minecraft.getInstance().level;
         } catch (Throwable ignored) {
            level = null;
         }
      }

      SodiumRgbBridge.begin(level, state, pos);

      try {
         invokeRenderModel(blockRenderer, model, state, pos, origin);
      } finally {
         SodiumRgbBridge.end();
      }
   }

   private static void invokeRenderModel(Object blockRenderer, Object model, BlockState state, BlockPos pos, BlockPos origin) {
      if (blockRenderer != null) {
         try {
            Method best = null;

            for (Method method : blockRenderer.getClass().getMethods()) {
               if ("renderModel".equals(method.getName())) {
                  Class<?>[] parameterTypes = method.getParameterTypes();
                  if (parameterTypes.length == 4
                     && parameterTypes[1].isInstance(state)
                     && parameterTypes[2].isInstance(pos)
                     && parameterTypes[3].isInstance(origin)) {
                     best = method;
                     break;
                  }
               }
            }

            if (best == null) {
               throw new NoSuchMethodException("Unable to find Sodium BlockRenderer.renderModel method");
            }

            best.invoke(blockRenderer, model, state, pos, origin);
         } catch (Throwable throwable) {
            Throwable cause = throwable.getCause() != null ? throwable.getCause() : throwable;
            if (cause instanceof RuntimeException runtimeException) {
               throw runtimeException;
            } else if (cause instanceof Error error) {
               throw error;
            } else {
               throw new RuntimeException(cause);
            }
         }
      }
   }

   private static Object readField(Object instance, String name) {
      if (instance == null) {
         return null;
      }

      Class<?> current = instance.getClass();

      while (current != null) {
         try {
            Field field = current.getDeclaredField(name);
            field.setAccessible(true);
            return field.get(instance);
         } catch (NoSuchFieldException ignored) {
            current = current.getSuperclass();
         } catch (Throwable ignored) {
            return null;
         }
      }

      return null;
   }
}
