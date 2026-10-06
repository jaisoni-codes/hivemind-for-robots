import sys
import os
sys.path.append(os.path.abspath('.'))
from hive_fastsim.simulator import Simulator
from hive_core.mutation import WorldAdapter

def test_l0_mutation():
    sim = Simulator()
    adapter = WorldAdapter(sim)
    
    # 1. Add
    adapter.mutate({
        "op": "add",
        "id": "pallet_1",
        "class": "pallet",
        "pose": [5.0, 5.0, 0.0]
    })
    assert len(sim.objects) == 1
    assert sim.objects['pallet_1']['class'] == 'pallet'
    
    # 2. Move
    adapter.mutate({
        "op": "move",
        "id": "pallet_1",
        "class": "pallet",
        "pose": [6.0, 6.0, 0.0]
    })
    assert sim.objects['pallet_1']['pose'] == [6.0, 6.0, 0.0]
    
    # 3. Remove
    adapter.mutate({
        "op": "remove",
        "id": "pallet_1"
    })
    assert len(sim.objects) == 0
    
    # Check log
    assert os.path.exists('world_events.log')
    with open('world_events.log', 'r') as f:
        lines = f.readlines()
        assert len(lines) == 3
