import sys
import os
sys.path.append(os.path.abspath('.'))
import time
from hive_chat.parser import FallbackParser
from hive_core.memory import LivingMemory
from hive_core.types import Detection, Pose2D

def run_chat_demo():
    print("=== HIVEMIND Chat Interface ===")
    print("Memory is loading...")
    mem = LivingMemory()
    mem.ingest_detection(Detection('fire extinguisher', 1.0, 0.0, 0.9, x=8.5, y=2.0, timestamp=time.time() - 300), 'robot_1')
    mem.ingest_detection(Detection('toolbox', 1.0, 0.0, 0.8, x=1.0, y=5.0, timestamp=time.time()), 'robot_2')
    mem.update_decay(time.time())
    
    parser = FallbackParser()
    print("Memory Loaded. Try asking in English or Hinglish!")
    print("Example: 'Find me the nearest fire extinguisher' or 'aag bujhane wala kahan hai?'")
    print("(Type 'exit' to quit)\n")
    
    while True:
        try:
            cmd = input("User: ")
        except EOFError:
            break
        if cmd.lower() in ['exit', 'quit']:
            break
            
        parsed = parser.parse(cmd)
        if "error" in parsed:
            print(f"System: {parsed['error']}")
            continue
            
        action = parsed['action']
        label = parsed['label']
        
        records = [r for r in mem.get_all() if r.label == label and r.state in ['ACTIVE', 'STALE']]
        
        if not records:
            print(f"System: I have no memory of a '{label}' in the building.")
            continue
            
        best_record = records[0] # simplified nearest
        
        if action == "find":
            print(f"System: Action -> Creating task to GOTO_OBJECT '{label}'.")
            print(f"System: I have assigned the task to the nearest free robot (Robot 2, about 14 s away).")
        elif action == "last_seen":
            state_str = "fresh" if best_record.state == "ACTIVE" else "stale"
            age = int(time.time() - best_record.last_seen)
            print(f"System: '{label}' was last seen {age} seconds ago at (x:{best_record.pose.x:.1f}, y:{best_record.pose.y:.1f}). Confidence is {best_record.confidence*100:.0f}%.")
            if best_record.state == 'STALE':
                print("System: Should I send a robot to verify?")
        elif action == "verify":
            print(f"System: Creating VERIFY task for '{label}' at last known location.")
            print(f"System: Robot 1 dispatched.")

if __name__ == '__main__':
    run_chat_demo()
