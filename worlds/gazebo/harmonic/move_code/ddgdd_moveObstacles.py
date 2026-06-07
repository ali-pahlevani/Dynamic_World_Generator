#!/usr/bin/env python3
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import time
import random
import math

from gz.transport13 import Node
from gz.msgs10.pose_pb2 import Pose
from gz.msgs10.boolean_pb2 import Boolean

prefix = "gz"
reqtype_prefix = "gz.msgs"
world_name = "ddgdd"

node = Node()

def set_pose(model_name, x, y, z):
    req = Pose()
    req.name = model_name
    req.position.x = x
    req.position.y = y
    req.position.z = z
    req.orientation.w = 1.0
    success, rep = node.request(f"/world/{world_name}/set_pose", req, Pose, Boolean, 500)
    return success

motions = {}
states = {}
motions["cylinder_2"] = {'type': 'linear', 'velocity': 1.0, 'std': 0.1, 'path': [(1.9, -0.6), (-0.4, 3.1)]}
states["cylinder_2"] = {'current_pos': [1.9, -0.6], 'direction': 1, 'start': [1.9, -0.6], 'end': [-0.4, 3.1], 'z': 0.5}

dt = 0.005
linear_dt = 0.001
while True:
    try:
        for model_name, motion in motions.items():
            state = states[model_name]
            velocity = max(min(random.gauss(motion["velocity"], motion["std"]), motion["velocity"] * 2), 0)
            delta = velocity * (linear_dt if motion["type"] == "linear" else dt)
            if motion["type"] == "linear":
                start = state["start"]
                end = state["end"]
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                length = math.sqrt(dx**2 + dy**2)
                if length < 0.001: continue
                unit_x = dx / length
                unit_y = dy / length
                new_x = state["current_pos"][0] + delta * state["direction"] * unit_x
                new_y = state["current_pos"][1] + delta * state["direction"] * unit_y
                t = ((new_x - start[0]) * dx + (new_y - start[1]) * dy) / (length**2)
                if t > 1:
                    new_x = end[0]
                    new_y = end[1]
                    state["direction"] = -state["direction"]
                elif t < 0:
                    new_x = start[0]
                    new_y = start[1]
                    state["direction"] = -state["direction"]
                else:
                    new_x = start[0] + t * dx
                    new_y = start[1] + t * dy
                state["current_pos"] = [new_x, new_y]
                if not set_pose(model_name, new_x, new_y, state["z"]):
                    exit(1)
            elif motion["type"] == "elliptical":
                delta_theta = velocity / (2 * math.pi * motion["semi_major"]) * 2 * math.pi * dt
                state["theta"] += delta_theta
                theta = state["theta"]
                x = state["center"][0] + motion["semi_major"] * math.cos(theta) * math.cos(motion["angle"]) - motion["semi_minor"] * math.sin(theta) * math.sin(motion["angle"])
                y = state["center"][1] + motion["semi_major"] * math.cos(theta) * math.sin(motion["angle"]) + motion["semi_minor"] * math.sin(theta) * math.cos(motion["angle"])
                if not set_pose(model_name, x, y, state["z"]):
                    exit(1)
            elif motion["type"] == "polygon":
                path = state["path"]
                start = path[state["current_segment"]]
                end = path[(state["current_segment"] + 1) % len(path)]
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                length = math.sqrt(dx**2 + dy**2)
                if length < 0.001: continue
                state["t"] += delta / length
                while state["t"] >= 1:
                    state["t"] -= 1
                    state["current_segment"] = (state["current_segment"] + 1) % len(path)
                start = path[state["current_segment"]]
                end = path[(state["current_segment"] + 1) % len(path)]
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                x = start[0] + state["t"] * dx
                y = start[1] + state["t"] * dy
                if not set_pose(model_name, x, y, state["z"]):
                    exit(1)
        time.sleep(linear_dt)
    except KeyboardInterrupt:
        exit(0)
