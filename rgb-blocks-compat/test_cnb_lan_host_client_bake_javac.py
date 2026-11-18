#!/usr/bin/env python3
"""Verify rapid C&B mesh recovery works on dedicated peers AND the LAN host.

The historical test setup was LAN multiplayer. The original C&B trailing
bake logic required Minecraft.getSingleplayerServer()==null, which excludes
the LAN HOST even when its BlockEntity is a valid client-side tile.

Compile the EXACT production isRemoteClientWorld() on Java17 and Java21
with dedicated, integrated-LAN, solo, stale world and server-side fixtures.
"""
from pathlib import Path
import subprocess,tempfile

path=Path("rgb-blocks-compat/recovered/fabric/com/rgbblocks/client/cnb/RGBCnbGeometryBakeDebouncer.java")
production=path.read_text(encoding="utf-8")
def exact_java_method(name):
    start=production.find(name)
    assert start>=0,("Production method missing",name)
    opening=production.index("{",start)
    depth=0
    for cursor in range(opening,len(production)):
        if production[cursor]=="{":depth+=1
        elif production[cursor]=="}":
            depth-=1
            if depth==0:return production[start:cursor+1]
    raise AssertionError(("Unbalanced Java method",name))

method=exact_java_method("private static boolean isRemoteClientWorld(Object tileEntity)")
assert "world.isClientSide()" in method
assert "mc.level == world" in method
assert "minecraft.level == level" in method
assert "getSingleplayerServer() == null" not in method
assert "return minecraft != null && minecraft.level == level;" in method

java=r'''import java.lang.reflect.Method;
public final class RGBCnbGeometryBakeDebouncer {
  static final class Level {
    private final boolean client;
    Level(boolean client){this.client=client;}
    boolean isClientSide(){return client;}
  }
  static final class Minecraft {
    private static final Minecraft MC=new Minecraft();
    Level level;
    Object server;
    static Minecraft getInstance(){return MC;}
    Object getSingleplayerServer(){return server;}
  }
  static class BlockEntity {
    Level level;
    BlockEntity(Level level){this.level=level;}
    Level getLevel(){return level;}
  }
  static class LegacyReflectiveTile {
    private final Level level;
    LegacyReflectiveTile(Level level){this.level=level;}
    public boolean hasLevel(){return level!=null;}
    public Level getLevel(){return level;}
  }
  /* ACTUAL_LAN_BAKE_WORLD_METHOD */
  static void require(boolean result,String reason){
    if(!result)throw new AssertionError(reason);
  }
  public static void main(String[] args) {
    Minecraft mc=Minecraft.getInstance();
    Level clientA=new Level(true);
    Level clientB=new Level(true);
    Level serverLevel=new Level(false);
    BlockEntity playerClient=new BlockEntity(clientA);
    mc.level=clientA;
    mc.server=null;
    require(isRemoteClientWorld(playerClient),
            "Dedicated remote peer C&B model update unexpectedly rejected");
    mc.server=new Object();
    require(isRemoteClientWorld(playerClient),
            "LAN multiplayer HOST client C&B model update rejected due to integrated server");
    require(isRemoteClientWorld(new LegacyReflectiveTile(clientA)),
            "LAN HOST legacy reflective C&B client tile rejected");
    require(!isRemoteClientWorld(new LegacyReflectiveTile(serverLevel)),
            "Integrated LAN SERVER tile was mistaken for a client mesh");
    require(!isRemoteClientWorld(new BlockEntity(serverLevel)),
            "Native integrated SERVER tile was mistaken for a client mesh");
    require(!isRemoteClientWorld(new BlockEntity(clientB)),
            "Stale client level from previous dimension accepted");
    require(!isRemoteClientWorld(new LegacyReflectiveTile(clientB)),
            "Stale reflection tile from other world accepted");
    require(!isRemoteClientWorld(new LegacyReflectiveTile(null)),
            "Worldless C&B tile accepted");
    require(!isRemoteClientWorld(new Object()),
            "Unrelated Java object accepted as C&B model tile");
    mc.server=null;
    require(isRemoteClientWorld(playerClient),
            "Solo integrated-type client lost C&B mesh update");
    mc.level=null;
    require(!isRemoteClientWorld(playerClient),
            "Disconnected peer applied stale C&B model update");
    System.out.println("RGB_PORT_CNB_LAN_HOST_CLIENT_REAL_JAVAC_PASS"+
      " remote_peer=true lan_host_client=true solo_client=true"+
      " server_side_false=true stale_world_false=true"+
      " reflection_fallback=true");
  }
}'''
java=java.replace("/* ACTUAL_LAN_BAKE_WORLD_METHOD */",method)
with tempfile.TemporaryDirectory(prefix="rgb-lan-cnb-") as temp:
    source_file=Path(temp)/"RGBCnbGeometryBakeDebouncer.java"
    source_file.write_text(java,encoding="utf-8")
    for version in ("17","21"):
        directory=Path(temp)/version
        directory.mkdir()
        compile=subprocess.run(["javac","--release",version,"-encoding","UTF-8",
                                "-d",str(directory),str(source_file)],
                   stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                   text=True,timeout=40)
        if compile.returncode:
            raise RuntimeError("C&B LAN host production method Java "+version+
                               " compile failed:\n"+compile.stdout[-6500:])
        run=subprocess.run(["java","-cp",str(directory),"RGBCnbGeometryBakeDebouncer"],
                           stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                           text=True,timeout=20)
        if run.returncode:
            raise RuntimeError("C&B LAN host production method Java "+version+
                               " failed:\n"+run.stdout[-6000:])
        assert "RGB_PORT_CNB_LAN_HOST_CLIENT_REAL_JAVAC_PASS" in run.stdout
        print("JAVA "+version+" "+run.stdout.strip(),flush=True)
