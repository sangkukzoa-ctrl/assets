#!/usr/bin/env python3
"""Exercise real RGB mesh oracle on Java17/21 with foreign non-public C&B APIs.

A public method exposed by a package-private Scena / C&B class can be found
with Class.getMethod(), yet Method.invoke() throws IllegalAccessException.
Unlike tests with all stubs nested in one Java class, this fixture uses
separate Java packages to reproduce true Minecraft cross-package access.
No user original source or C&B runtime download is needed for this regression.
"""
from pathlib import Path
import subprocess
import tempfile

source = Path(
    "rgb-blocks-compat/recovered/fabric/com/rgbblocks/client/cnb/RGBCnbMeshIntegrity.java"
).read_text(encoding="utf-8")


def extract(signature):
    start = source.find(signature)
    assert start >= 0, ("Missing original production helper", signature)
    opening = source.index("{", start)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise AssertionError(("Unbalanced original production method", signature))


real_java = "\n\n".join([
    extract("private static boolean hasActualVoxelStates("),
    extract("private static Method findZeroArg("),
])
assert 'method.setAccessible(true)' in real_java
assert 'findZeroArg(information.getClass(),"blockState")' in real_java
assert 'findZeroArg(information.getClass(),"getBlockState")' in real_java

test_java = r'''import fixture.HiddenApiFixtures;
import java.lang.reflect.Method;
import java.util.Map;

public final class CnbForeignClassAccessTest {
    static final class BlockState {
        private final boolean air;
        BlockState(boolean air) { this.air = air; }
        public boolean isAir() { return air; }
    }
    static final class BlockEntity {
        private final Object stats;
        BlockEntity(Object stats) { this.stats = stats; }
        public Object getStatistics() { return stats; }
    }
    /* EXACT_PRODUCTION_HELPERS */

    private static void require(boolean value, String reason) {
        if (!value) throw new AssertionError(reason);
    }
    public static void main(String[] args) throws Exception {
        BlockState glow = new BlockState(false);
        BlockState air = new BlockState(true);
        Object neo = HiddenApiFixtures.neoInformation(glow);
        Object forge = HiddenApiFixtures.forgeInformation(glow);
        Object empty = HiddenApiFixtures.neoInformation(air);
        Object neoStats = HiddenApiFixtures.stats(Map.of(neo, 4095, empty, 1));
        Object forgeStats = HiddenApiFixtures.stats(Map.of(forge, 4095));
        require(hasActualVoxelStates(new BlockEntity(neoStats)),
                "Neo package-private BlockInformation wrapper lost 4095 glow bits");
        require(hasActualVoxelStates(new BlockEntity(forgeStats)),
                "Forge package-private IBlockInformation wrapper lost glow bits");
        require(!hasActualVoxelStates(new BlockEntity(
                    HiddenApiFixtures.stats(Map.of(empty, 4096)))),
                "AIR-only C&B microbits are not rendered quads");
        require(!hasActualVoxelStates(new BlockEntity(
                    HiddenApiFixtures.stats(Map.of(neo, 0)))),
                "Zero-count colored voxel data must not count as geometry");
        require(findZeroArg(neo.getClass(), "blockState").invoke(neo) == glow,
                "Public method from hidden class must actually be INVOCABLE");
        require(findZeroArg(forge.getClass(), "getBlockState").invoke(forge) == glow,
                "Hidden legacy accessor must actually be INVOCABLE");
        boolean absent = false;
        try { findZeroArg(neo.getClass(), "noSuchMethod"); }
        catch (NoSuchMethodException valid) { absent = true; }
        require(absent, "Missing C&B method must not silently pass");
        System.out.println("RGB_PORT_CNB_FOREIGN_NONPUBLIC_API_REAL_JAVAC_PASS" +
                " forge_info=true neo_info=true hidden_stats=true" +
                " air_only_rejected=true zero_bits_rejected=true missing_api_rejected=true");
    }
}'''.replace("/* EXACT_PRODUCTION_HELPERS */", real_java)

fixture_java = r'''package fixture;
import java.util.Map;

public final class HiddenApiFixtures {
    private HiddenApiFixtures() {}
    public static Object neoInformation(Object material) {
        return new HiddenNeoInformation(material);
    }
    public static Object forgeInformation(Object material) {
        return new HiddenForgeInformation(material);
    }
    public static Object stats(Map<?, ?> map) {
        return new HiddenStatistics(map);
    }
}
// These THREE classes deliberately cannot be named/imported by RGB.
final class HiddenNeoInformation {
    private final Object state;
    HiddenNeoInformation(Object state) { this.state = state; }
    public Object blockState() { return state; }
}
final class HiddenForgeInformation {
    private final Object state;
    HiddenForgeInformation(Object state) { this.state = state; }
    public Object getBlockState() { return state; }
}
final class HiddenStatistics {
    private final Map<?, ?> counts;
    HiddenStatistics(Map<?, ?> counts) { this.counts = counts; }
    public Map<?, ?> getStateCounts() { return counts; }
}'''

with tempfile.TemporaryDirectory(prefix="rgb-cnb-foreign-") as directory:
    root = Path(directory)
    oracle = root / "CnbForeignClassAccessTest.java"
    fixture = root / "fixture" / "HiddenApiFixtures.java"
    fixture.parent.mkdir(parents=True)
    oracle.write_text(test_java, encoding="utf-8")
    fixture.write_text(fixture_java, encoding="utf-8")
    for version in ("17", "21"):
        classes = root / ("java" + version)
        classes.mkdir()
        cmd = ["javac", "--release", version, "-encoding", "UTF-8",
               "-d", str(classes), str(oracle), str(fixture)]
        compile = subprocess.run(
            cmd, text=True, capture_output=True, timeout=50
        )
        if compile.returncode:
            raise RuntimeError("Real C&B foreign API test compilation failed Java " +
                               version + ":\n" + compile.stdout[-5000:] +
                               compile.stderr[-5000:])
        executed = subprocess.run(
            ["java", "-cp", str(classes), "CnbForeignClassAccessTest"],
            text=True, capture_output=True, timeout=25
        )
        if executed.returncode:
            raise RuntimeError("Real C&B cross-package access failed Java " +
                               version + ":\n" + executed.stdout[-5000:] +
                               executed.stderr[-5000:])
        assert "RGB_PORT_CNB_FOREIGN_NONPUBLIC_API_REAL_JAVAC_PASS" in executed.stdout
        print("JAVA " + version + " " + executed.stdout.strip(), flush=True)
