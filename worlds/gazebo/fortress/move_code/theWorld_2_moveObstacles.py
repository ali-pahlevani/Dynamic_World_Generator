#!/usr/bin/env python3
import subprocess
import time
import random
import math

prefix = "ign"
reqtype_prefix = "ignition.msgs"
world_name = "theWorld_2"

def set_pose(model_name, x, y, z):
    request_str = f'name: "{model_name}", position {{ x: {x} y: {y} z: {z} }}, orientation {{ w: 1 }}'
    cmd = [prefix, "service", "-s", f"/world/{world_name}/set_pose", "--reqtype", f"{reqtype_prefix}.Pose", "--reptype", f"{reqtype_prefix}.Boolean", "--timeout", "300", "--req", request_str]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to set pose for {model_name}: {result.stderr}")
        return False
    return True

motions = {}
states = {}
motions["box_5"] = {'type': 'polygon', 'velocity': 5.0, 'std': 0.01, 'path': [(-0.6, -1.6), (1.0, -1.0), (0.3, -0.2), (-1.1, -0.7), (-0.6, -1.6)]}
states["box_5"] = {'current_segment': 0, 't': 0.0, 'path': [[-0.6, -1.6], [1.0, -1.0], [0.3, -0.2], [-1.1, -0.7], [-0.6, -1.6]], 'z': 0.25}

dt = 0.01
while True:
    try:
        for model_name, motion in motions.items():
            state = states[model_name]
            velocity = random.gauss(motion["velocity"], motion["std"])
            delta = velocity * dt
            if motion["type"] == "linear":
                start = state["start"]
                end = state["end"]
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                length = math.sqrt(dx**2 + dy**2)
                unit_x = dx / length
                unit_y = dy / length
                new_x = state["current_pos"][0] + delta * state["direction"] * unit_x
                new_y = state["current_pos"][1] + delta * state["direction"] * unit_y
                dist_to_end = math.hypot(new_x - end[0], new_y - end[1])
                dist_to_start = math.hypot(new_x - start[0], new_y - start[1])
                if state["direction"] > 0 and dist_to_end < 0.01:
                    new_x = end[0]
                    new_y = end[1]
                    state["direction"] = -state["direction"]
                elif state["direction"] < 0 and dist_to_start < 0.01:
                    new_x = start[0]
                    new_y = start[1]
                    state["direction"] = -state["direction"]
                state["current_pos"] = [new_x, new_y]
                if not set_pose(model_name, new_x, new_y, state["z"]):
                    print(f"Stopping script as set_pose failed for {model_name}")
                    exit(1)
            elif motion["type"] == "elliptical":
                delta_theta = velocity / (2 * math.pi * motion["semi_major"]) * 2 * math.pi * dt
                state["theta"] += delta_theta
                theta = state["theta"]
                x = state["center"][0] + motion["semi_major"] * math.cos(theta) * math.cos(motion["angle"]) - motion["semi_minor"] * math.sin(theta) * math.sin(motion["angle"])
                y = state["center"][1] + motion["semi_major"] * math.cos(theta) * math.sin(motion["angle"]) + motion["semi_minor"] * math.sin(theta) * math.cos(motion["angle"])
                if not set_pose(model_name, x, y, state["z"]):
                    print(f"Stopping script as set_pose failed for {model_name}")
                    exit(1)
            elif motion["type"] == "polygon":
                path = state["path"]
                start = path[state["current_segment"]]
                end = path[(state["current_segment"] + 1) % len(path)]
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                length = math.sqrt(dx**2 + dy**2)
                state["t"] += delta / length
                if state["t"] >= 1:
                    state["current_segment"] = (state["current_segment"] + 1) % len(path)
                    state["t"] = max(0, state["t"] - 1)
                t = min(1, state["t"])
                x = start[0] + t * dx
                y = start[1] + t * dy
                if not set_pose(model_name, x, y, state["z"]):
                    print(f"Stopping script as set_pose failed for {model_name}")
                    exit(1)
        time.sleep(dt)
    except KeyboardInterrupt:
        print("Motion script interrupted")
        exit(0)
