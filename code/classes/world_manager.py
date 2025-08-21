import os
import subprocess
import time
import math
from xml.etree import ElementTree as ET
from utils.color_utils import get_color
from utils.config import PROJECT_ROOT, WORLDS_GAZEBO_DIR

class WorldManager:
    def __init__(self, simulation, version):
        self.simulation = simulation
        self.version = version
        self.sdf_version = "1.8" if version == "fortress" else "1.9"
        self.world_path = None
        self.world_name = None
        self.models = []
        self.sdf_tree = None
        self.sdf_root = None
        self.process = None
        self.script_process = None
        self.base_dir = PROJECT_ROOT  # Use PROJECT_ROOT from config.py

    def create_new_world(self, world_name):
        self.world_name = world_name
        empty_world_path = os.path.join(WORLDS_GAZEBO_DIR, self.version, "empty_world.sdf")
        print(f"Looking for empty world at: {empty_world_path}")
        if not os.path.exists(empty_world_path):
            raise FileNotFoundError(f"Empty world file not found: {empty_world_path}")

        if self.version == "fortress":
            cmd = ["ign", "gazebo", empty_world_path]
        else:
            cmd = ["gz", "sim", empty_world_path]
        self.process = subprocess.Popen(cmd)
        self.world_path = os.path.join(WORLDS_GAZEBO_DIR, self.version, f"{world_name}.sdf")
        print(f"Creating world at: {self.world_path}")
        self.models = []
        self.sdf_tree = ET.parse(empty_world_path)
        self.sdf_root = self.sdf_tree.getroot()
        self.world_name = self.sdf_root.find("world").get("name")

    def load_world(self, world_name):
        self.world_name = world_name
        self.world_path = os.path.join(WORLDS_GAZEBO_DIR, self.version, f"{world_name}.sdf")
        print(f"Loading world at: {self.world_path}")
        if not os.path.exists(self.world_path):
            raise FileNotFoundError(f"World file not found: {self.world_path}")

        if self.version == "fortress":
            cmd = ["ign", "gazebo", self.world_path]
        else:
            cmd = ["gz", "sim", self.world_path]
        self.process = subprocess.Popen(cmd)

        self.sdf_tree = ET.parse(self.world_path)
        self.sdf_root = self.sdf_tree.getroot()
        self.world_name = self.sdf_root.find("world").get("name")
        self.models = []

        # Inverse color mapping to convert RGB back to color name
        rgb_to_color = {
            (0, 0, 0): "Black",
            (0.5, 0.5, 0.5): "Gray",
            (1, 1, 1): "White",
            (1, 0, 0): "Red",
            (0, 0, 1): "Blue",
            (0, 1, 0): "Green"
        }

        for model_elem in self.sdf_root.findall(".//model"):
            name = model_elem.get("name")
            motion_elem = model_elem.find(".//motion")
            print(f"Loading model: {name}, Motion: {motion_elem is not None}")
            type_elem = model_elem.find("type")
            model_type = type_elem.text if type_elem is not None else None

            if model_type is None:
                geometry = model_elem.find(".//geometry")
                if geometry is not None:
                    if geometry.find("box") is not None:
                        model_type = "wall" if "wall" in name else "box"
                    elif geometry.find("cylinder") is not None:
                        model_type = "cylinder"
                    elif geometry.find("sphere") is not None:
                        model_type = "sphere"
                    else:
                        model_type = "unknown"

            properties = {}
            pose_str = model_elem.find("pose").text
            pose = [float(x) for x in pose_str.split()]
            x, y, z, _, _, yaw = pose

            # Parse color from <material><diffuse>
            material = model_elem.find(".//material/diffuse")
            color_name = "Gray"  # Default
            if material is not None:
                rgb = tuple(float(x) for x in material.text.split()[:3])  # Get first three values (R, G, B)
                color_name = rgb_to_color.get(rgb, "Gray")  # Map RGB to color name, default to Gray

            geometry = model_elem.find(".//geometry")
            if geometry:
                if model_type in ["wall", "box"]:
                    size_str = geometry.find("box/size").text
                    size = [float(s) for s in size_str.split()]
                    if model_type == "wall":
                        length, width, height = size
                        dx = (length / 2) * math.cos(yaw)
                        dy = (length / 2) * math.sin(yaw)
                        start_x = x - dx
                        start_y = y - dy
                        end_x = x + dx
                        end_y = y + dy

                        properties = {
                            "start": (start_x, start_y),
                            "end": (end_x, end_y),
                            "width": width,
                            "height": height,
                            "color": color_name
                        }
                    else:
                        properties = {
                            "position": (x, y, z),
                            "size": size,
                            "color": color_name
                        }
                elif model_type == "cylinder":
                    radius = float(geometry.find("cylinder/radius").text)
                    length = float(geometry.find("cylinder/length").text)
                    properties = {
                        "position": (x, y, z),
                        "size": (radius, length),
                        "color": color_name
                    }
                elif model_type == "sphere":
                    radius = float(geometry.find("sphere/radius").text)
                    properties = {
                        "position": (x, y, z),
                        "size": (radius,),
                        "color": color_name
                    }

            # Parse motion if present (for dynamic obstacles)
            motion_elem = model_elem.find(".//motion")
            if motion_elem is not None:
                motion = {"type": motion_elem.find("type").text}
                velocity = motion_elem.find("velocity")
                if velocity is not None:
                    motion["velocity"] = float(velocity.text)
                std = motion_elem.find("std")
                if std is not None:
                    motion["std"] = float(std.text)
                if motion["type"] in ["linear", "polygon"]:
                    path = []
                    for point_elem in motion_elem.findall("point"):
                        x = float(point_elem.find("x").text)
                        y = float(point_elem.find("y").text)
                        path.append((x, y))
                    motion["path"] = path
                elif motion["type"] == "elliptical":
                    motion["semi_major"] = float(motion_elem.find("semi_major").text)
                    motion["semi_minor"] = float(motion_elem.find("semi_minor").text)
                    motion["angle"] = float(motion_elem.find("angle").text)
                properties["motion"] = motion

            self.models.append({
                "name": name,
                "type": model_type,
                "properties": properties,
                "status": ""
            })

    def add_model(self, model):
        for existing_model in self.models:
            if existing_model["name"] == model["name"]:
                existing_model.update(model)
                return
        self.models.append(model)

    def apply_changes(self):
        if not self.process or self.process.poll() is not None:
            raise RuntimeError("Gazebo simulation is not running. Please create or load a world first.")

        time.sleep(2)

        prefix = "ign" if self.version == "fortress" else "gz"
        reqtype_prefix = "ignition.msgs" if self.version == "fortress" else "gz.msgs"

        for model in self.models[:]:
            if model["status"] == "updated":
                request_str = f'name: "{model["name"]}", type: 2'
                cmd = [prefix, "service", "-s", f"/world/{self.world_name}/remove",
                    "--reqtype", f"{reqtype_prefix}.Entity",
                    "--reptype", f"{reqtype_prefix}.Boolean",
                    "--timeout", "3000",
                    "--req", request_str]
                print("Executing command:", " ".join(cmd))
                result = subprocess.run(cmd, capture_output=True, text=True)
                print("Result stdout:", result.stdout)
                print("Result stderr:", result.stderr)
                if result.returncode != 0:
                    print(f"Warning: Failed to remove model {model['name']} for update: {result.stderr}")
                    continue
                for elem in self.sdf_root.findall(f".//model[@name='{model['name']}']"):
                    self.sdf_root.find("world").remove(elem)
                self.save_sdf(self.world_path)
                model["status"] = "new"

            if model["status"] == "new":
                sdf_snippet_service = self.generate_model_sdf(model, for_service=True)
                sdf_escaped = sdf_snippet_service.replace('"', '\\"')
                sdf_compact = ' '.join(sdf_escaped.split())
                request_str = f'sdf: "{sdf_compact}"'
                cmd = [prefix, "service", "-s", f"/world/{self.world_name}/create",
                    "--reqtype", f"{reqtype_prefix}.EntityFactory",
                    "--reptype", f"{reqtype_prefix}.Boolean",
                    "--timeout", "3000",
                    "--req", request_str]
                print("Executing command:", " ".join(cmd))
                result = subprocess.run(cmd, capture_output=True, text=True)
                print("Result stdout:", result.stdout)
                print("Result stderr:", result.stderr)
                if result.returncode != 0 or "data: true" not in result.stdout:
                    print(f"Warning: Failed to add model {model['name']}: {result.stderr}")
                    continue
                time.sleep(1)
                sdf_snippet_file = self.generate_model_sdf(model, for_service=False)
                model_elem = ET.fromstring(sdf_snippet_file)
                for elem in self.sdf_root.findall(f".//model[@name='{model['name']}']"):
                    self.sdf_root.find("world").remove(elem)
                self.sdf_root.find("world").append(model_elem)
                self.save_sdf(self.world_path)
            elif model["status"] == "removed":
                request_str = f'name: "{model["name"]}", type: 2'
                cmd = [prefix, "service", "-s", f"/world/{self.world_name}/remove",
                    "--reqtype", f"{reqtype_prefix}.Entity",
                    "--reptype", f"{reqtype_prefix}.Boolean",
                    "--timeout", "3000",
                    "--req", request_str]
                print("Executing command:", " ".join(cmd))
                result = subprocess.run(cmd, capture_output=True, text=True)
                print("Result stdout:", result.stdout)
                print("Result stderr:", result.stderr)
                if result.returncode != 0:
                    print(f"Warning: Failed to remove model {model['name']}: {result.stderr}")
                    continue
                for elem in self.sdf_root.findall(f".//model[@name='{model['name']}']"):
                    self.sdf_root.find("world").remove(elem)
                self.save_sdf(self.world_path)

        dynamic_models = [m for m in self.models if "motion" in m["properties"]]
        if dynamic_models:
            move_code_dir = os.path.join(WORLDS_GAZEBO_DIR, self.version, "move_code")
            os.makedirs(move_code_dir, exist_ok=True)
            script_path = os.path.join(move_code_dir, f"{self.world_name}_moveObstacles.py")
            with open(script_path, 'w') as f:
                f.write('#!/usr/bin/env python3\n')
                f.write('import time\n')
                f.write('import random\n')
                f.write('import math\n\n')
                if self.version == "harmonic":
                    f.write('from gz.transport13 import Node\n')
                    f.write('from gz.msgs10.pose_pb2 import Pose\n')
                    f.write('from gz.msgs10.boolean_pb2 import Boolean\n\n')
                else:
                    f.write('import subprocess\n\n')
                f.write(f'prefix = "{"ign" if self.version == "fortress" else "gz"}\"\n')
                f.write(f'reqtype_prefix = "{"ignition.msgs" if self.version == "fortress" else "gz.msgs"}\"\n')
                f.write(f'world_name = "{self.world_name}"\n\n')
                if self.version == "harmonic":
                    f.write('node = Node()\n\n')
                    f.write('def set_pose(model_name, x, y, z):\n')
                    f.write('    req = Pose()\n')
                    f.write('    req.name = model_name\n')
                    f.write('    req.position.x = x\n')
                    f.write('    req.position.y = y\n')
                    f.write('    req.position.z = z\n')
                    f.write('    req.orientation.w = 1.0\n')
                    f.write('    success, rep = node.request(f"/world/{world_name}/set_pose", req, Pose, Boolean, 500)\n')
                    f.write('    return success\n\n')
                else:
                    f.write('def set_pose(model_name, x, y, z):\n')
                    f.write('    request_str = f\'name: "{model_name}", position {{ x: {x} y: {y} z: {z} }}, orientation {{ w: 1 }}\'\n')
                    f.write('    cmd = [prefix, "service", "-s", f"/world/{world_name}/set_pose", "--reqtype", f"{reqtype_prefix}.Pose", "--reptype", f"{reqtype_prefix}.Boolean", "--timeout", "500", "--req", request_str]\n')
                    f.write('    result = subprocess.run(cmd, capture_output=True, text=True)\n')
                    f.write('    if result.returncode != 0:\n')
                    f.write('        print(f"Failed to set pose for {model_name}: {result.stderr}")\n')
                    f.write('        return False\n')
                    f.write('    return True\n\n')
                f.write('motions = {}\nstates = {}\n')
                for m in dynamic_models:
                    motion = m["properties"]["motion"]
                    z = m["properties"]["position"][2]
                    state = {}
                    if motion["type"] == "linear":
                        start, end = motion["path"]
                        state = {'current_pos': list(start), 'direction': 1, 'start': list(start), 'end': list(end), 'z': z}
                    elif motion["type"] == "elliptical":
                        state = {'theta': 0.0, 'center': list(m["properties"]["position"][:2]), 'semi_major': motion["semi_major"], 'semi_minor': motion["semi_minor"], 'angle': motion["angle"], 'z': z}
                    elif motion["type"] == "polygon":
                        state = {'current_segment': 0, 't': 0.0, 'path': [list(p) for p in motion["path"]], 'z': z}
                    f.write(f'motions["{m["name"]}"] = {motion}\n')
                    f.write(f'states["{m["name"]}"] = {state}\n')
                f.write('\ndt = 0.005\nlinear_dt = 0.001\nwhile True:\n')
                f.write('    try:\n')
                f.write('        for model_name, motion in motions.items():\n')
                f.write('            state = states[model_name]\n')
                f.write('            velocity = max(min(random.gauss(motion["velocity"], motion["std"]), motion["velocity"] * 2), 0)\n')
                f.write('            delta = velocity * (linear_dt if motion["type"] == "linear" else dt)\n')
                f.write('            if motion["type"] == "linear":\n')
                f.write('                start = state["start"]\n')
                f.write('                end = state["end"]\n')
                f.write('                dx = end[0] - start[0]\n')
                f.write('                dy = end[1] - start[1]\n')
                f.write('                length = math.sqrt(dx**2 + dy**2)\n')
                f.write('                if length < 0.001: continue\n')
                f.write('                unit_x = dx / length\n')
                f.write('                unit_y = dy / length\n')
                f.write('                new_x = state["current_pos"][0] + delta * state["direction"] * unit_x\n')
                f.write('                new_y = state["current_pos"][1] + delta * state["direction"] * unit_y\n')
                f.write('                t = ((new_x - start[0]) * dx + (new_y - start[1]) * dy) / (length**2)\n')
                f.write('                if t > 1:\n')
                f.write('                    new_x = end[0]\n')
                f.write('                    new_y = end[1]\n')
                f.write('                    state["direction"] = -state["direction"]\n')
                f.write('                elif t < 0:\n')
                f.write('                    new_x = start[0]\n')
                f.write('                    new_y = start[1]\n')
                f.write('                    state["direction"] = -state["direction"]\n')
                f.write('                else:\n')
                f.write('                    new_x = start[0] + t * dx\n')
                f.write('                    new_y = start[1] + t * dy\n')
                f.write('                state["current_pos"] = [new_x, new_y]\n')
                f.write('                if not set_pose(model_name, new_x, new_y, state["z"]):\n')
                f.write('                    print(f"Stopping script as set_pose failed for {model_name}")\n')
                f.write('                    exit(1)\n')
                f.write('            elif motion["type"] == "elliptical":\n')
                f.write('                delta_theta = velocity / (2 * math.pi * motion["semi_major"]) * 2 * math.pi * dt\n')
                f.write('                state["theta"] += delta_theta\n')
                f.write('                theta = state["theta"]\n')
                f.write('                x = state["center"][0] + motion["semi_major"] * math.cos(theta) * math.cos(motion["angle"]) - motion["semi_minor"] * math.sin(theta) * math.sin(motion["angle"])\n')
                f.write('                y = state["center"][1] + motion["semi_major"] * math.cos(theta) * math.sin(motion["angle"]) + motion["semi_minor"] * math.sin(theta) * math.cos(motion["angle"])\n')
                f.write('                if not set_pose(model_name, x, y, state["z"]):\n')
                f.write('                    print(f"Stopping script as set_pose failed for {model_name}")\n')
                f.write('                    exit(1)\n')
                f.write('            elif motion["type"] == "polygon":\n')
                f.write('                path = state["path"]\n')
                f.write('                start = path[state["current_segment"]]\n')
                f.write('                end = path[(state["current_segment"] + 1) % len(path)]\n')
                f.write('                dx = end[0] - start[0]\n')
                f.write('                dy = end[1] - start[1]\n')
                f.write('                length = math.sqrt(dx**2 + dy**2)\n')
                f.write('                if length < 0.001: continue\n')
                f.write('                state["t"] += delta / length\n')
                f.write('                while state["t"] >= 1:\n')
                f.write('                    state["t"] -= 1\n')
                f.write('                    state["current_segment"] = (state["current_segment"] + 1) % len(path)\n')
                f.write('                start = path[state["current_segment"]]\n')
                f.write('                end = path[(state["current_segment"] + 1) % len(path)]\n')
                f.write('                dx = end[0] - start[0]\n')
                f.write('                dy = end[1] - start[1]\n')
                f.write('                x = start[0] + state["t"] * dx\n')
                f.write('                y = start[1] + state["t"] * dy\n')
                f.write('                if not set_pose(model_name, x, y, state["z"]):\n')
                f.write('                    print(f"Stopping script as set_pose failed for {model_name}")\n')
                f.write('                    exit(1)\n')
                f.write('        time.sleep(linear_dt if motion["type"] == "linear" else dt)\n')
                f.write('    except KeyboardInterrupt:\n')
                f.write('        print("Motion script interrupted")\n')
                f.write('        exit(0)\n')
            os.chmod(script_path, 0o755)

            launch_path = os.path.join(WORLDS_GAZEBO_DIR, self.version, "move_code", f"{self.world_name}_launch.sh")
            with open(launch_path, 'w') as f:
                f.write('#!/bin/bash\n')
                if self.version == "fortress":
                    f.write(f'ign gazebo {self.world_path} &\n')
                else:
                    f.write(f'gz sim {self.world_path} &\n')
                f.write('sleep 2\n')
                f.write(f'python3 {script_path} &\n')
                f.write('wait\n')
            os.chmod(launch_path, 0o755)

            if self.script_process and self.script_process.poll() is None:
                self.script_process.terminate()
                try:
                    self.script_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.script_process.kill()
            self.script_process = subprocess.Popen(['python3', script_path])

        self.models = [m for m in self.models if m["status"] != "removed"]
        for model in self.models:
            model["status"] = ""

    def cleanup(self):
        import signal
        print("Starting cleanup of WorldManager")
        
        # Save the current world state before closing
        if self.sdf_tree and self.world_path:
            try:
                self.save_sdf(self.world_path)
                print(f"Saved world state to {self.world_path}")
            except Exception as e:
                print(f"Warning: Failed to save world state: {str(e)}")

        # Terminate the motion script process
        if self.script_process and self.script_process.poll() is None:
            print(f"Terminating motion script process (PID: {self.script_process.pid})")
            try:
                # Send SIGINT first for graceful shutdown
                self.script_process.send_signal(signal.SIGINT)
                self.script_process.wait(timeout=2)
                print("Motion script process terminated gracefully")
            except subprocess.TimeoutExpired:
                print("Motion script process did not terminate gracefully, sending SIGTERM")
                self.script_process.terminate()
                try:
                    self.script_process.wait(timeout=2)
                    print("Motion script process terminated with SIGTERM")
                except subprocess.TimeoutExpired:
                    print("Motion script process still running, sending SIGKILL")
                    self.script_process.kill()
                    self.script_process.wait(timeout=2)
                    print("Motion script process killed")
            except Exception as e:
                print(f"Error terminating motion script process: {str(e)}")
            self.script_process = None

        # Terminate the Gazebo process
        if self.process and self.process.poll() is None:
            print(f"Terminating Gazebo process (PID: {self.process.pid})")
            try:
                # Send SIGINT first for graceful shutdown
                self.process.send_signal(signal.SIGINT)
                self.process.wait(timeout=2)
                print("Gazebo process terminated gracefully")
            except subprocess.TimeoutExpired:
                print("Gazebo process did not terminate gracefully, sending SIGTERM")
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                    print("Gazebo process terminated with SIGTERM")
                except subprocess.TimeoutExpired:
                    print("Gazebo process still running, sending SIGKILL")
                    self.process.kill()
                    self.process.wait(timeout=2)
                    print("Gazebo process killed")
            except Exception as e:
                print(f"Error terminating Gazebo process: {str(e)}")
            self.process = None
        print("Cleanup completed")

    def generate_model_sdf(self, model, for_service=False):
        model_type = model["type"]
        props = model["properties"]
        color_rgb = get_color(props["color"])

        if model_type == "wall":
            start = props["start"]
            end = props["end"]
            center_x = (start[0] + end[0]) / 2
            center_y = (start[1] + end[1]) / 2
            z = props["height"] / 2
            length = ((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5
            yaw = math.atan2(end[1] - start[1], end[0] - start[0])
            pose = f"{center_x:.6f} {center_y:.6f} {z:.6f} 0 0 {yaw:.6f}"
            size = (length, props["width"], props["height"])
            size_str = f"{size[0]:.6f} {size[1]:.6f} {size[2]:.6f}"
        else:
            x, y, z = props["position"]
            pose = f"{x:.6f} {y:.6f} {z:.6f} 0 0 0"
            size = props["size"]
            if model_type == "box":
                size_str = f"{size[0]:.6f} {size[1]:.6f} {size[2]:.6f}"
            elif model_type == "cylinder":
                size_str = f"{size[0]:.6f} {size[1]:.6f}"
            elif model_type == "sphere":
                size_str = f"{size[0]:.6f}"

        static_str = "false" if "motion" in model["properties"] else "true"
        sdf = f"""<model name='{model["name"]}'>
            <static>{static_str}</static>
            <type>{model_type}</type>
            <pose>{pose}</pose>
            <link name='link'>
                <collision name='collision'>
                    <geometry>"""
        if model_type in ["wall", "box"]:
            sdf += f"""<box><size>{size_str}</size></box>"""
        elif model_type == "cylinder":
            sdf += f"""<cylinder><radius>{size[0]:.6f}</radius><length>{size[1]:.6f}</length></cylinder>"""
        elif model_type == "sphere":
            sdf += f"""<sphere><radius>{size[0]:.6f}</radius></sphere>"""
        sdf += f"""</geometry>
                </collision>
                <visual name='visual'>
                    <geometry>"""
        if model_type in ["wall", "box"]:
            sdf += f"""<box><size>{size_str}</size></box>"""
        elif model_type == "cylinder":
            sdf += f"""<cylinder><radius>{size[0]:.6f}</radius><length>{size[1]:.6f}</length></cylinder>"""
        elif model_type == "sphere":
            sdf += f"""<sphere><radius>{size[0]:.6f}</radius></sphere>"""
        sdf += f"""</geometry>
                    <material>
                        <diffuse>{color_rgb[0]} {color_rgb[1]} {color_rgb[2]} 1</diffuse>
                    </material>
                </visual>"""
        if not static_str == "true":  # Only for dynamic models
            # Calculate mass and inertia (assume density=1000 kg/m^3 for realism)
            density = 1000.0
            if model_type in ["wall", "box"]:
                w, l, h = map(float, size_str.split())
                mass = density * w * l * h
                ixx = mass / 12.0 * (l**2 + h**2)
                iyy = mass / 12.0 * (w**2 + h**2)
                izz = mass / 12.0 * (w**2 + l**2)
            elif model_type == "cylinder":
                r, h = map(float, size_str.split())
                mass = density * math.pi * r**2 * h
                ixx = mass / 12.0 * (3 * r**2 + h**2)
                iyy = ixx
                izz = mass / 2.0 * r**2
            elif model_type == "sphere":
                r = float(size_str)
                mass = density * (4/3) * math.pi * r**3
                ixx = (2/5) * mass * r**2
                iyy = ixx
                izz = ixx
            inertial_str = f"""<inertial>
                <mass>{mass:.6f}</mass>
                <inertia>
                    <ixx>{ixx:.6f}</ixx><ixy>0</ixy><ixz>0</ixz>
                    <iyy>{iyy:.6f}</iyy><iyz>0</iyz>
                    <izz>{izz:.6f}</izz>
                </inertia>
            </inertial>"""
            sdf += inertial_str
            sdf += "<gravity>false</gravity>"
        sdf += """</link>"""
        if "motion" in props:
            motion = props["motion"]
            sdf += "<motion>"
            sdf += f"<type>{motion['type']}</type>"
            sdf += f"<velocity>{motion['velocity']:.6f}</velocity>"
            sdf += f"<std>{motion['std']:.6f}</std>"
            if "path" in motion:
                for p in motion["path"]:
                    sdf += f"<point><x>{p[0]:.6f}</x><y>{p[1]:.6f}</y></point>"
            if "semi_major" in motion:
                sdf += f"<semi_major>{motion['semi_major']:.6f}</semi_major>"
                sdf += f"<semi_minor>{motion['semi_minor']:.6f}</semi_minor>"
                sdf += f"<angle>{motion['angle']:.6f}</angle>"
            sdf += "</motion>"
        sdf += "</model>"
        if for_service:
            sdf = f"""<sdf version='{self.sdf_version}'>{sdf}</sdf>"""
        return sdf

    def save_sdf(self, path):
        if self.sdf_tree:
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)  # Ensure directory exists
                self.sdf_tree.write(path, encoding="utf-8", xml_declaration=True)
                print(f"Saved SDF to {path}")
            except Exception as e:
                print(f"Error saving SDF to {path}: {str(e)}")
                raise