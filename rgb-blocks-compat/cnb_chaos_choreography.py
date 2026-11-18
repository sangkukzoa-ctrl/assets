#!/usr/bin/env python3
"""Owner-style hostile RGB/C&B game test. CI only, two REAL clients on one server.

A printed seed plus JSONL transcript reproduces the exact order and pauses.
Scripted chaos is separate from baseline acceptance, with strict two-client
per-round RGB color, genuine voxel-count and baked-mesh oracles.
"""
import json
import os
import random
import time
from pathlib import Path

PALETTE=("redstone_block","diamond_block","emerald_block","redstone_block")
COLOR=("rgb_red_186_72_96_glow","rgb_blue_8_85_209_glow",
       "rgb_green_59_209_25_glow","rgb_red_186_72_96_glow")

# Always exercise EVERY high-risk class even when a random seed is unlucky.
# The rest of each round remains seeded and genuinely randomized. This does
# not enlarge the 64-action default or slow down real dual-client CI.
HOSTILE_ACTIONS=("bake","bake","bake","bake","mode","tp","remove",
                 "reinstall","near_glow","occlude","chunk_churn",
                 "stone_replace","color_spoof","mode_pulse")
MUST_COVER=("bake","mode","tp","remove","reinstall","near_glow",
            "occlude","chunk_churn","stone_replace","color_spoof",
            "mode_pulse")

def exercise(*,send,server,server_lines,first,first_lines,second,second_lines,
             wait_server,wait_first,wait_second,evidence,seed,log):
    rng=random.Random(seed)
    per_round=int(os.environ.get("RGB_PORT_CHAOS_ACTIONS_PER_ROUND","64"))
    assert 24<=per_round<=500, "Chaos actions per round must be 24..500"
    assert per_round>=len(MUST_COVER), "Insufficient actions for mandatory hostility coverage"
    evidence=Path(evidence)
    events=evidence/"cnb-chaos-events.jsonl"
    events.parent.mkdir(parents=True,exist_ok=True)
    total=0
    def trace(kind,detail,extra=None):
        nonlocal total
        total+=1
        rec={"seed":seed,"sequence":total,"kind":kind,"detail":detail,
             "monotonic":round(time.monotonic(),4)}
        if extra is not None:rec["extra"]=extra
        with events.open("a",encoding="utf-8") as out:
            out.write(json.dumps(rec,sort_keys=True,ensure_ascii=False)+"\n")
        log("CHAOS_TRACE "+json.dumps(rec,sort_keys=True))
    def command(text,delay=None):
        trace("command",text)
        send(server,text)
        if delay is not None:time.sleep(delay)
    trace("begin","seeded 2-client churn / repeated C&B removal / RGB modes / bakes",
          {"actions_per_round":per_round,"bake_storm_per_round":24})
    # Independent C&B chunk, far from the original live/mixed fixtures.
    command("forceload add 32 0",0.25)
    command("forceload add 160 0",0.25)
    command("fill 27 119 -3 43 119 14 minecraft:stone",0.25)
    command("fill 156 119 -3 174 119 14 minecraft:stone",0.25)
    command("setblock 32 121 7 rgbblocks:rgb_red_186_72_96_glow",0.25)
    # Prevent the immediate next baseline scene from inheriting MANUAL.
    def teleport_far():
        command("tp RGBPortTester 161.5 120 0.5 facing 166.5 121.5 7.5")
        command("tp RGBPortPeer 162.5 120 0.5 facing 166.5 121.5 7.5")
    def teleport_near():
        command("tp RGBPortTester 28.5 120 0.5 facing 32.5 121.5 7.5")
        command("tp RGBPortPeer 29.5 120 0.5 facing 32.5 121.5 7.5")
    for round_id,(material,expected) in enumerate(zip(PALETTE,COLOR)):
        trace("round_start",round_id,{"color":expected})
        command(f"setblock 166 120 10 minecraft:{material}",0.2)
        # Alternate sane and absurd action pauses, including near-simultaneous
        # server commands; NEVER silently skip a test because it looks harsh.
        # A forced coverage set (at unpredictable shuffled positions) means
        # every seed exercises all of: loaded/unloaded source chunks, inverse
        # color occlusion, mid-race C&B block replacement, and mode pulses.
        # Remaining commands are truly random and still use the old seed.
        plan=list(MUST_COVER)+[
            rng.choice(HOSTILE_ACTIONS) for _ in range(per_round-len(MUST_COVER))
        ]
        rng.shuffle(plan)
        covered={action:0 for action in MUST_COVER}
        for index,action in enumerate(plan):
            if action in covered:covered[action]+=1
            interval=rng.choice((0.0,0.0,0.005,0.015,0.045,0.08,0.18,0.5))
            if action=="bake":
                command("rgb bake",interval)
            elif action=="mode":
                command("rgb "+rng.choice(("manual","auto")),interval)
            elif action=="tp":
                (teleport_near if rng.random()<0.5 else teleport_far)()
                time.sleep(interval)
            elif action=="remove":
                command("setblock 166 121 7 minecraft:air",interval)
            elif action=="reinstall":
                command("setblock 166 121 7 chiselsandbits:chiseled",interval)
            elif action=="stone_replace":
                # Not a valid C&B tile: make stale pending microbit packets
                # prove that they do not resurrect an earlier RGB source.
                command("setblock 166 121 7 minecraft:stone",interval)
            elif action=="near_glow":
                command("setblock 32 121 7 "+rng.choice((
                   "minecraft:air","rgbblocks:rgb_red_186_72_96_glow",
                   "rgbblocks:rgb_blue_8_85_209_glow")),interval)
            elif action=="occlude":
                # Rapidly modulate real light occlusion next to the source.
                command("setblock 167 121 7 "+rng.choice((
                   "minecraft:air","minecraft:stone","minecraft:glass",
                   "rgbblocks:rgb_red_186_72_96_glass")),interval)
            elif action=="chunk_churn":
                # Temporarily drop and re-pin the near (NOT oracle) chunk.
                # This provokes asynchronous rebuild/neighbor broadcasts,
                # without invalidating the distant dual-client C&B fixture.
                command("forceload remove 32 0")
                command("forceload add 32 0",interval)
            elif action=="color_spoof":
                # Flip the sculptor's color marker while a prior tile update
                # may still be inflight. Final round marker is restored below.
                command("setblock 166 120 10 minecraft:"+rng.choice((
                    "redstone_block","diamond_block","emerald_block")),interval)
            elif action=="mode_pulse":
                # Deliberately ridiculous near-zero-gap mode and Bake race.
                command("rgb manual")
                command("rgb bake",0.0)
                command("rgb auto",interval)
            else:
                raise AssertionError("Unknown owner-chaos action "+repr(action))
        assert all(covered.values()),("Chaos omitted mandatory action",seed,round_id,covered)
        trace("round_coverage",round_id,{"operations":covered,"random_tail":
              per_round-len(MUST_COVER),"seed":seed})
        # The last sampled color must not inherit a random prior round.
        # Also clean up extra occluders so an unrelated neighbor emitter
        # cannot satisfy or hide the actual C&B RGB color oracle.
        command("forceload add 32 0")
        command("forceload add 160 0")
        command("setblock 167 121 7 minecraft:air",0.02)
        command(f"setblock 166 120 10 minecraft:{material}",0.02)
        # Additional near-zero-spacing MANUAL bake storm to provoke races.
        command("rgb manual")
        for burst in range(24):
            command("rgb bake",0.0 if burst%3 else 0.01)
        # End every noisy round with a true NEW C&B entity, real 4095-bit
        # sculpture, and a forced fully committed AUTO bake for strict oracle.
        command("setblock 166 121 7 minecraft:air",0.15)
        before_server=len(server_lines)
        command("setblock 166 121 7 chiselsandbits:chiseled")
        target="RGB_PORT_CHAOS_SCULPT_PASS color="+expected
        assert wait_server(server_lines,target,before_server,server,100,
                           "chaos_real_CnB_sculpt_"+str(round_id)), (
            "Chaos server failed to produce NEW 4095-bit "+expected+" C&B at round "+str(round_id))
        command("rgb auto",0.35)
        command("rgb setbake all",0.25)
        teleport_far()
        command("rgb bake",0.75)
        # Unique per-round marker is sent only AFTER final server sculpt,
        # so a historical pass cannot satisfy a newer mutated round.
        before_first=len(first_lines);before_second=len(second_lines)
        command(f"setblock 166 120 {11+round_id} minecraft:gold_block")
        marker=f"RGB_PORT_CHAOS_ROUND_PASS round={round_id} color={expected}"
        assert wait_first(first_lines,marker,before_first,first,120,
                          "first_CNB_mesh_and_RGB_round_"+str(round_id)), (
            "First client lost C&B real voxels, mesh quads or colored neighbor at round "+str(round_id))
        assert wait_second(second_lines,marker,before_second,second,120,
                           "second_CNB_mesh_and_RGB_round_"+str(round_id)), (
            "Second client lost C&B real voxels, mesh quads or colored neighbor at round "+str(round_id))
        assert first.poll() is None and second.poll() is None, (
            "Chaos disconnected or crashed one real client at round "+str(round_id))
        trace("round_pass",round_id,{"color":expected,"two_clients":True})
    command("rgb auto",0.25)
    command("tp RGBPortTester -1.5 120 0.5 facing 0.5 121.5 7.5")
    command("tp RGBPortPeer 1.5 120 0.5 facing 0.5 121.5 7.5")
    trace("complete","all four rounds, two live clients, 4095 voxels, adjacent RGB and BakedModel quads")
    return {"seed":seed,"rounds_passed":4,"two_clients_verified":True,
            "actions_per_round":per_round,"bake_storms":96,
            "actions_recorded":total,"transcript":str(events),
            "mandatory_hostile_actions_per_round":len(MUST_COVER),
            "hostile_action_families":list(MUST_COVER)}
