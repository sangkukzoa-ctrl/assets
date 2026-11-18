#!/usr/bin/env python3
"""Offline deterministic contract test for the REAL 2-client hostile chaos plan.

Executes the exact production cnb_chaos_choreography.exercise() with simulated
server/client acknowledgements and no delays. Proves every round covers all
11 mandatory action families, two-client oracle markers are unique/fresh,
source chunks and occluders are restored, action timing is bounded, repeated
seeds reproduce identical server commands, and different seeds perturb them.

This is the CHOREOGRAPHY preflight only, not a Minecraft gameplay PASS.
"""
import importlib.util
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

SCRIPT=Path("rgb-blocks-compat/cnb_chaos_choreography.py")
spec=importlib.util.spec_from_file_location("rgb_cnb_chaos_choreography",SCRIPT)
chaos=importlib.util.module_from_spec(spec)
spec.loader.exec_module(chaos)
assert len(chaos.MUST_COVER)==11
assert len(set(chaos.MUST_COVER))==11

class Client:
    def poll(self):return None

def run(seed,per_round=64):
    commands=[]
    passed=[]
    server_lines=[]
    first_lines=[]
    second_lines=[]
    def send(_server,cmd):
        commands.append(cmd)
    def await_log(lines,marker,before,process,seconds,label):
        assert seconds<=150,("Chaos runtime oracle timeout unexpectedly large",label,seconds)
        assert process.poll() is None
        assert marker not in lines[before:],("Old response reused as NEW oracle pass",marker)
        lines.append(marker)
        passed.append((label,marker))
        return True
    with tempfile.TemporaryDirectory(prefix="rgb-offline-chaos-") as scratch:
        with patch.object(chaos.time,"sleep",lambda _:None):
            with patch.dict(os.environ,{"RGB_PORT_CHAOS_ACTIONS_PER_ROUND":str(per_round)}):
                result=chaos.exercise(send=send,server=Client(),server_lines=server_lines,
                    first=Client(),first_lines=first_lines,second=Client(),
                    second_lines=second_lines,wait_server=await_log,
                    wait_first=await_log,wait_second=await_log,
                    evidence=Path(scratch),seed=seed,log=lambda *_:None)
        path=Path(result["transcript"])
        assert path.exists()
        events=[json.loads(v) for v in path.read_text("utf-8").splitlines()]
    return commands,passed,events,result

for seed in (1313131,2718281,0,42,999999937):
    commands,passes,events,result=run(seed)
    assert result["rounds_passed"]==4
    assert result["two_clients_verified"] is True
    assert result["bake_storms"]==96
    assert result["actions_per_round"]==64
    assert result["mandatory_hostile_actions_per_round"]==11
    assert result["actions_recorded"]==len(events)
    assert len(commands)<1000, "Bizarre stress actions exceed bounded test budget"
    assert [evt["sequence"] for evt in events]==list(range(1,len(events)+1))
    assert all(evt["seed"]==seed for evt in events)
    cover=[e for e in events if e["kind"]=="round_coverage"]
    assert len(cover)==4,("Not all 4 RGB colors passed mandatory stress",seed)
    for n,round_event in enumerate(cover):
        assert round_event["detail"]==n
        counted=round_event["extra"]["operations"]
        assert set(counted)==set(chaos.MUST_COVER)
        assert all(v>=1 for v in counted.values())
        assert sum(counted.values())<=64
        assert round_event["extra"]["random_tail"]==53
    assert len(passes)==12, "Expected four server and EIGHT live-client passes"
    for n,wanted in enumerate(chaos.COLOR):
        expected="RGB_PORT_CHAOS_ROUND_PASS round="+str(n)+" color="+wanted
        oracle_hits=[m for _,m in passes if m==expected]
        assert len(oracle_hits)==2,(seed,n,oracle_hits)
        assert any("SCULPT_PASS color="+wanted in mark for _,mark in passes)
        assert f"setblock 166 120 {11+n} minecraft:gold_block" in commands
        assert f"setblock 166 120 10 minecraft:{chaos.PALETTE[n]}" in commands
    assert commands.count("forceload add 32 0")>=5
    assert commands.count("forceload add 160 0")==5
    assert commands.count("setblock 167 121 7 minecraft:air")>=4
    assert commands[-3:]==[
        "rgb auto",
        "tp RGBPortTester -1.5 120 0.5 facing 0.5 121.5 7.5",
        "tp RGBPortPeer 1.5 120 0.5 facing 0.5 121.5 7.5",
    ]
    assert len([x for x in commands if x=="rgb bake"])>=96
    again,_,_,_=run(seed)
    assert commands==again,("Chaos with same seed was not exactly reproducible",seed)
    different,_,_,_=run(seed+1)
    assert commands!=different,("Distinct chaos seeds didn't change ordering",seed)
    print("RGB_PORT_CHAOS_PLAN_SEED_PASS",seed,"commands",len(commands),
          "rounds",len(cover),"must_cover",len(chaos.MUST_COVER),flush=True)

# Validate the exposed 24-action minimum. Mandatory coverage must remain
# complete even when other tests shrink the random action budget.
short,_,rounds,small=run(12,24)
assert small["actions_per_round"]==24
assert len([v for v in rounds if v["kind"]=="round_coverage"])==4
print("RGB_PORT_CHAOS_CHOREOGRAPHY_OFFLINE_PASS",
      "seeds=5 rounds_per_seed=4 mandatory_action_families=11 "
      "two_real_client_oracle_slots_per_round=2 zero_real_game_claims=true",
      flush=True)
