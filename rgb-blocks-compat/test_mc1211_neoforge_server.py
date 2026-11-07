#!/usr/bin/env python3
"""RGB Blocks 1.3.1 / Minecraft 1.21.1 NeoForge native server acceptance.

A real production NeoForge 21.1.265 server with Chisels & Bits 21.1.32:
registries, command dispatch, three RGB block variants, persistent mode/bake,
save/stop and reopening. This does NOT validate client pixels, sculpted bits,
two-client synchronization or shaders.
"""
import json
import pathlib
import shutil
import subprocess
import threading
import time
import urllib.request
import zipfile

ROOT = pathlib.Path("mc1211-neoforge-runtime")
MODS = ROOT / "mods"
MODS.mkdir(parents=True, exist_ok=True)
BUILD = pathlib.Path("port-work/mc1211-neoforge/build/libs")
JARS = [p for p in BUILD.glob("*.jar") if not p.name.endswith(("-sources.jar", "-dev.jar"))]
assert JARS, "Native NeoForge JAR missing; build the mod before server test"
JAR = max(JARS, key=lambda p: p.stat().st_size)
with zipfile.ZipFile(JAR) as z:
    entries = z.namelist()
    palette = json.loads(z.read("assets/rgbblocks/palette.json"))
    assert len(palette) == 16687, len(palette)
    assert "META-INF/neoforge.mods.toml" in entries, "Wrong loader: not a NeoForge JAR"
    assert sum(n.startswith("assets/rgbblocks/blockstates/") and n.endswith(".json") for n in entries) == 50061
    assert sum(n.startswith("assets/rgbblocks/models/block/") and n.endswith(".json") for n in entries) == 50061
    assert sum(n.endswith(".png") for n in entries) == 33377
    candidate = next(c for c in palette if int(c["red"]) > 180 and int(c["green"]) < 100 and int(c["blue"]) < 100)
    name = "rgbblocks:rgb_%s_%d_%d_%d" % (candidate["group"], candidate["red"], candidate["green"], candidate["blue"])
shutil.copy2(JAR, MODS / "RGBBlocks-1.3.1-MC1.21.1-NeoForge.jar")
print("Native NeoForge JAR / palette verified:", JAR, name, flush=True)

def fetch(url, destination):
    request = urllib.request.Request(url, headers={"User-Agent": "RGBBlocks-1.3.1-NeoForge-Integration-Test/1.0"})
    with urllib.request.urlopen(request, timeout=240) as response:
        data = response.read()
    destination.write_bytes(data)
    print("DOWNLOADED", destination, len(data), flush=True)

fetch("https://maven.neoforged.net/releases/net/neoforged/neoforge/21.1.265/neoforge-21.1.265-installer.jar",
      ROOT / "neoforge-installer.jar")
fetch("https://mediafilez.forgecdn.net/files/7405/270/chisels-and-bits-neoforge-21.1.32.jar",
      MODS / "chisels-and-bits-neoforge-21.1.32.jar")

installed = subprocess.run(["java", "-jar", "neoforge-installer.jar", "--installServer"],
    cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=450)
(ROOT / "installer.log").write_text(installed.stdout, encoding="utf-8")
assert installed.returncode == 0 and (ROOT / "run.sh").exists(), (
    "NeoForge installer failed (last log lines):\n" + installed.stdout[-5000:])
(ROOT / "eula.txt").write_text("eula=true\n", encoding="utf-8")
(ROOT / "user_jvm_args.txt").write_text("-Xms512M\n-Xmx5G\n", encoding="utf-8")
(ROOT / "server.properties").write_text(
    "online-mode=false\nserver-ip=127.0.0.1\nserver-port=25565\n"
    "motd=RGB Blocks 1.21.1 native NeoForge integration test\n"
    "max-players=2\nview-distance=4\nsimulation-distance=4\n"
    "enable-command-block=true\nwhite-list=true\n", encoding="utf-8")

def cycle(label, commands):
    process = subprocess.Popen(["bash", "./run.sh", "nogui"], cwd=ROOT,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1)
    lines = []
    def pump():
        for line in process.stdout:
            lines.append(line)
            if ("ERROR" in line or "Exception" in line or "RGB " in line
                    or "Done (" in line or "FATAL" in line):
                print(label, line.rstrip(), flush=True)
    reader = threading.Thread(target=pump, daemon=True)
    reader.start()
    ready = False
    start = time.monotonic()
    while time.monotonic() - start < 420:
        if process.poll() is not None:
            break
        if any("Done (" in x and "For help" in x for x in lines):
            ready = True
            break
        time.sleep(.7)
    if ready:
        for command in commands:
            process.stdin.write(command + "\n")
            process.stdin.flush()
            time.sleep(1.15)
        time.sleep(4)
    if process.poll() is None:
        process.stdin.write("stop\n")
        process.stdin.flush()
    try:
        process.wait(timeout=80)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)
    reader.join(timeout=5)
    log = "".join(lines)
    (ROOT / (label + ".log")).write_text(log, encoding="utf-8")
    crash_terms = (
        "MixinApplyError", "MixinTransformerError", "NoClassDefFoundError",
        "NoSuchMethodError", "ModLoadingException", "Failed to start the minecraft server")
    fatal = [s for s in crash_terms if s.lower() in log.lower()]
    result = {
        "phase": label, "started": ready, "exit_code": process.returncode,
        "palette_16687": "16687" in log, "rgb_command_response": "RGB mode:" in log,
        "cnb_loaded": ("chiselsandbits" in log.lower() or "chisels-and-bits" in log.lower()),
        "fatal_patterns": fatal, "world_created": (ROOT / "world").exists(),
        "log": label + ".log"
    }
    print("CYCLE RESULT", json.dumps(result, ensure_ascii=False), flush=True)
    print("TAIL:\n", "\n".join(log.splitlines()[-22:]), flush=True)
    return result, log

first, log_first = cycle("first-launch", [
    "rgb get", "rgb bake get", "forceload add 0 0",
    f"setblock 0 120 0 {name}",
    f"setblock 1 120 0 {name}_glow",
    f"setblock 2 120 0 {name}_glass",
    f"execute if block 0 120 0 {name} run say RGB_NORMAL_PERSIST_PASS",
    f"execute if block 1 120 0 {name}_glow run say RGB_GLOW_PERSIST_PASS",
    f"execute if block 2 120 0 {name}_glass run say RGB_GLASS_PERSIST_PASS",
    "rgb manual", "rgb setbake all", "rgb bake", "rgb get"
])
if first["started"] and not first["fatal_patterns"]:
    second, log_second = cycle("reopen-world", [
        f"execute if block 0 120 0 {name} run say RGB_NORMAL_PERSIST_PASS",
        f"execute if block 1 120 0 {name}_glow run say RGB_GLOW_PERSIST_PASS",
        f"execute if block 2 120 0 {name}_glass run say RGB_GLASS_PERSIST_PASS",
        "rgb get", "rgb bake get", "rgb bake"
    ])
else:
    second, log_second = {"started": False, "reason": "first launch failed"}, ""

result = {
    "version": "Minecraft 1.21.1", "loader": "NeoForge 21.1.265",
    "mod": "RGB Blocks 1.3.1", "chisels_and_bits": "NeoForge 21.1.32",
    "scope": "Production dedicated server: native loader/registry/commands/block save-reload",
    "limitations": "Not C&B sculpting, RGB visual light accuracy, shaders or multiple clients",
    "jar": JAR.name, "color": name, "first": first, "reopen": second
}
(ROOT / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
assert first["started"], "NeoForge+RGB+C&B dedicated server did not reach READY"
assert first["exit_code"] == 0, "First server shutdown failed"
assert first["cnb_loaded"], "Chisels & Bits not detected in runtime log"
assert not first["fatal_patterns"], "Fatal classloading/mixin issue"
assert first["palette_16687"], "RGB full palette registration absent"
assert first["rgb_command_response"], "RGB command not registered"
assert second["started"] and second["exit_code"] == 0, "Saved world did not reopen cleanly"
assert not second["fatal_patterns"] and second["rgb_command_response"], "RGB commands failed on reload"
for marker in ("RGB_NORMAL_PERSIST_PASS", "RGB_GLOW_PERSIST_PASS", "RGB_GLASS_PERSIST_PASS"):
    assert marker in log_first, marker + " missing from initial placement"
    assert marker in log_second, marker + " missing after world reload"
assert "Unknown or incomplete command" not in log_first + log_second, "Original /rgb bake get alias missing"
assert "Unknown command" not in log_first + log_second, "An original RGB command was not recognized"
assert "RGB mode: MANUAL" in log_second, "Manual mode was not saved"
assert "Bake scope: ALL" in log_second, "Bake scope was not saved"
print("PASS: Native NeoForge 1.21.1 + RGB Blocks 1.3.1 + C&B 21.1.32 dedicated server", flush=True)
