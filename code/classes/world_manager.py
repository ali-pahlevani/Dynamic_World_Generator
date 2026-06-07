import os
import re
import signal
import subprocess
import time
import math
from xml.etree import ElementTree as ET
from utils.color_utils import get_color
from utils.config import PROJECT_ROOT, WORLDS_GAZEBO_DIR

_VALID_WORLD_NAME = re.compile(r'^[A-Za-z0-9_]+$')
_NUMBERED_NAME_RE = re.compile(r'^(.+)_(\d+)$')


class WorldManager:
    def __init__(self, simulation, version):
        self.simulation = simulation
        self.version = version
        if version == "fortress":
            self.sdf_version = "1.8"
        elif version == "ionic":
            self.sdf_version = "1.12"
        else:
            self.sdf_version = "1.9"
        self.world_path = None
        self.world_name = None
        self.models = []
        self.sdf_tree = None
        self.sdf_root = None
        self.process = None
        self.script_process = None
        self.base_dir = PROJECT_ROOT
        self._gazebo_ready = False
        self._process_start_time = 0.0

    def create_new_world(self, world_name):
        self.world_name = world_name
        empty_world_path = os.path.join(WORLDS_GAZEBO_DIR, self.version, "empty_world.sdf")
        if not os.path.exists(empty_world_path):
            raise FileNotFoundError(f"Empty world file not found: {empty_world_path}")

        cmd = ["ign", "gazebo", empty_world_path] if self.version == "fortress" else ["gz", "sim", empty_world_path]
        self.process = subprocess.Popen(cmd)
        self.world_path = os.path.join(WORLDS_GAZEBO_DIR, self.version, f"{world_name}.sdf")
        self.models = []
        self.sdf_tree = ET.parse(empty_world_path)
        self.sdf_root = self.sdf_tree.getroot()
        self.world_name = self.sdf_root.find("world").get("name")

    def load_world(self, world_name):
        self.world_name = world_name
        self.world_path = os.path.join(WORLDS_GAZEBO_DIR, self.version, f"{world_name}.sdf")
        if not os.path.exists(self.world_path):
            raise FileNotFoundError(f"World file not found: {self.world_path}")

        cmd = ["ign", "gazebo", self.world_path] if self.version == "fortress" else ["gz", "sim", self.world_path]
        self.process = subprocess.Popen(cmd)
        self._process_start_time = time.time()
        self._gazebo_ready = False

        self.sdf_tree = ET.parse(self.world_path)
        self.sdf_root = self.sdf_tree.getroot()
        self.world_name = self.sdf_root.find("world").get("name")
        self.models = []

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
            pose_elem = model_elem.find("pose")
            if pose_elem is None or not pose_elem.text:
                continue
            pose = [float(v) for v in pose_elem.text.split()]
            x, y, z, _, _, yaw = pose

            material = model_elem.find(".//material/diffuse")
            color_name = "Gray"
            if material is not None:
                rgb = tuple(float(v) for v in material.text.split()[:3])
                color_name = rgb_to_color.get(rgb, "Gray")

            geometry = model_elem.find(".//geometry")
            if geometry:
                if model_type in ["wall", "box"]:
                    size_str = geometry.find("box/size").text
                    size = [float(s) for s in size_str.split()]
                    if model_type == "wall":
                        length, width, height = size
                        dx = (length / 2) * math.cos(yaw)
                        dy = (length / 2) * math.sin(yaw)
                        properties = {
                            "start": (x - dx, y - dy),
                            "end": (x + dx, y + dy),
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
                        px = float(point_elem.find("x").text)
                        py = float(point_elem.find("y").text)
                        path.append((px, py))
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
                reused_removed = existing_model["status"] == "removed"
                existing_model.update(model)
                if reused_removed:
                    # The freed-up name belonged to a model that is still (or
                    # was) live in Gazebo — delete that entity, then create
                    # this one in its place, instead of overwriting "removed".
                    existing_model["status"] = "updated"
                return
        self.models.append(model)

    def _renumber_models(self):
        """Close numbering gaps left by removed models, e.g. wall_1, wall_3
        becomes wall_1, wall_2 (and similarly box_/cylinder_/sphere_, each
        numbered independently) once Apply is pushed.

        Gazebo has no rename service, so a model that is already live there
        can only be renamed by deleting the old-named entity and creating a
        new-named one with the same properties; entries that were never
        pushed (status "new") are simply renamed in place. All deletions are
        applied before any creation so a freed-up name is never claimed
        before its previous occupant is gone.
        """
        groups = {}
        for m in self.models:
            if m["status"] == "removed":
                continue
            match = _NUMBERED_NAME_RE.match(m["name"])
            if match:
                groups.setdefault(match.group(1), []).append((m, int(match.group(2))))

        removals, creations = [], []
        for prefix, members in groups.items():
            members.sort(key=lambda pair: pair[1])
            for idx, (m, _) in enumerate(members, start=1):
                new_name = f"{prefix}_{idx}"
                if m["name"] == new_name:
                    continue
                if m["status"] == "new":
                    m["name"] = new_name
                    continue
                removals.append({
                    "name": m["name"],
                    "type": m["type"],
                    "properties": dict(m["properties"]),
                    "status": "removed",
                })
                m["name"] = new_name
                m["status"] = "new"
                creations.append(m)

        if removals or creations:
            creation_ids = {id(m) for m in creations}
            remaining = [m for m in self.models if id(m) not in creation_ids]
            self.models = remaining + removals + creations

    def apply_changes(self):
        """Push pending model changes to the running Gazebo simulation.

        Returns a list of (model_name, error_message) tuples for every model
        that failed to be applied.  An empty list means full success.
        """
        if not self.process or self.process.poll() is not None:
            raise RuntimeError(
                "Gazebo simulation is not running. "
                "Please create or load a world first."
            )

        if not _VALID_WORLD_NAME.match(self.world_name or ""):
            raise RuntimeError(
                f"World name '{self.world_name}' is not a valid Gazebo service name.\n"
                "World names may only contain letters, numbers, and underscores — "
                "no spaces or special characters.\n"
                f"Rename the world to: {re.sub(r'[^A-Za-z0-9_]', '_', self.world_name or 'my_world')}"
            )

        prefix = "ign" if self.version == "fortress" else "gz"
        print(f"[DWG] apply_changes — world='{self.world_name}' version={self.version}")
        if not self._gazebo_ready:
            # `gz service --list` is unreliable for discovery (multicast may
            # never return the world service even when it is running).  A
            # simple elapsed-time guard is more predictable: Gazebo needs ~4 s
            # to register its transport services after startup.  If the user
            # took longer than that to draw objects, no sleep is needed.
            elapsed = time.time() - self._process_start_time
            wait = max(0.0, 4.0 - elapsed)
            if wait > 0.05:
                print(f"[DWG] Waiting {wait:.1f}s for Gazebo services to register …")
                time.sleep(wait)
            self._gazebo_ready = True
        reqtype_prefix = "ignition.msgs" if self.version == "fortress" else "gz.msgs"
        SERVICE_TIMEOUT = "5000"

        # Stop any running motion script BEFORE touching entities.
        # If the old script keeps sending set_pose calls during remove/create,
        # Gazebo logs floods of "Unable to update pose for entity id:[0]".
        if self.script_process and self.script_process.poll() is None:
            self.script_process.terminate()
            try:
                self.script_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.script_process.kill()
                self.script_process.wait(timeout=2)
            self.script_process = None

        self._renumber_models()

        errors = []          # (name, message)
        applied_names = set()  # models successfully pushed to Gazebo

        for model in self.models[:]:
            name = model["name"]

            # ── updated: delete existing, then re-create ─────────────────
            if model["status"] == "updated":
                req = f'name: "{name}", type: 2'
                cmd = [prefix, "service", "-s",
                       f"/world/{self.world_name}/remove",
                       "--reqtype", f"{reqtype_prefix}.Entity",
                       "--reptype", f"{reqtype_prefix}.Boolean",
                       "--timeout", SERVICE_TIMEOUT,
                       "--req", req]
                print(f"[DWG]   remove '{name}' …")
                r = subprocess.run(cmd, capture_output=True, text=True)
                print(f"[DWG]     rc={r.returncode}  stdout={r.stdout.strip()!r}"
                      f"  stderr={r.stderr.strip()!r}")
                if r.returncode == 0:
                    for elem in self.sdf_root.findall(
                            f".//model[@name='{name}']"):
                        self.sdf_root.find("world").remove(elem)
                    self.save_sdf(self.world_path)
                model["status"] = "new"   # fall through to creation

            # ── new: create ───────────────────────────────────────────────
            if model["status"] == "new":
                sdf_service = self.generate_model_sdf(model, for_service=True)
                sdf_escaped = sdf_service.replace('"', '\\"')
                sdf_compact = " ".join(sdf_escaped.split())
                req = f'sdf: "{sdf_compact}"'
                cmd = [prefix, "service", "-s",
                       f"/world/{self.world_name}/create",
                       "--reqtype", f"{reqtype_prefix}.EntityFactory",
                       "--reptype", f"{reqtype_prefix}.Boolean",
                       "--timeout", SERVICE_TIMEOUT,
                       "--req", req]
                print(f"[DWG]   create '{name}' ({model['type']}) …")
                r = subprocess.run(cmd, capture_output=True, text=True)
                print(f"[DWG]     rc={r.returncode}  stdout={r.stdout.strip()!r}"
                      f"  stderr={r.stderr.strip()!r}")
                if r.returncode != 0 or "data: true" not in r.stdout:
                    detail = (r.stderr.strip() or r.stdout.strip()
                              or "no response from Gazebo service")
                    errors.append((name, detail))
                    # Keep status="new" so the user can retry
                    continue
                time.sleep(0.5)
                sdf_file = self.generate_model_sdf(model, for_service=False)
                model_elem = ET.fromstring(sdf_file)
                for elem in self.sdf_root.findall(f".//model[@name='{name}']"):
                    self.sdf_root.find("world").remove(elem)
                self.sdf_root.find("world").append(model_elem)
                self.save_sdf(self.world_path)
                applied_names.add(name)

            # ── removed: delete ───────────────────────────────────────────
            elif model["status"] == "removed":
                req = f'name: "{name}", type: 2'
                cmd = [prefix, "service", "-s",
                       f"/world/{self.world_name}/remove",
                       "--reqtype", f"{reqtype_prefix}.Entity",
                       "--reptype", f"{reqtype_prefix}.Boolean",
                       "--timeout", SERVICE_TIMEOUT,
                       "--req", req]
                print(f"[DWG]   delete '{name}' …")
                r = subprocess.run(cmd, capture_output=True, text=True)
                print(f"[DWG]     rc={r.returncode}  stdout={r.stdout.strip()!r}"
                      f"  stderr={r.stderr.strip()!r}")
                if r.returncode != 0:
                    detail = r.stderr.strip() or r.stdout.strip() or "remove failed"
                    errors.append((name, detail))
                    continue
                for elem in self.sdf_root.findall(f".//model[@name='{name}']"):
                    self.sdf_root.find("world").remove(elem)
                self.save_sdf(self.world_path)
                applied_names.add(name)

        dynamic_models = [m for m in self.models
                          if m["status"] != "removed" and "motion" in m["properties"]]
        if dynamic_models:
            move_code_dir = os.path.join(WORLDS_GAZEBO_DIR, self.version, "move_code")
            os.makedirs(move_code_dir, exist_ok=True)
            script_path = os.path.join(move_code_dir, f"{self.world_name}_moveObstacles.py")
            with open(script_path, 'w') as f:
                f.write('#!/usr/bin/env python3\n')
                # Must be set before any gz/protobuf import to work around
                # protobuf >= 4.x C-extension incompatibility with older stubs.
                f.write('import os\n')
                f.write('os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"\n')
                f.write('import time\n')
                f.write('import random\n')
                f.write('import math\n\n')
                if self.version == "harmonic":
                    f.write('from gz.transport13 import Node\n')
                    f.write('from gz.msgs10.pose_pb2 import Pose\n')
                    f.write('from gz.msgs10.boolean_pb2 import Boolean\n\n')
                elif self.version == "ionic":
                    f.write('from gz.transport14 import Node\n')
                    f.write('from gz.msgs11.pose_pb2 import Pose\n')
                    f.write('from gz.msgs11.boolean_pb2 import Boolean\n\n')
                else:
                    f.write('import subprocess\n\n')
                prefix_val = "ign" if self.version == "fortress" else "gz"
                reqtype_val = "ignition.msgs" if self.version == "fortress" else "gz.msgs"
                f.write(f'prefix = "{prefix_val}"\n')
                f.write(f'reqtype_prefix = "{reqtype_val}"\n')
                f.write(f'world_name = "{self.world_name}"\n\n')
                if self.version in ("harmonic", "ionic"):
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
                f.write('                    exit(1)\n')
                f.write('            elif motion["type"] == "elliptical":\n')
                f.write('                delta_theta = velocity / (2 * math.pi * motion["semi_major"]) * 2 * math.pi * dt\n')
                f.write('                state["theta"] += delta_theta\n')
                f.write('                theta = state["theta"]\n')
                f.write('                x = state["center"][0] + motion["semi_major"] * math.cos(theta) * math.cos(motion["angle"]) - motion["semi_minor"] * math.sin(theta) * math.sin(motion["angle"])\n')
                f.write('                y = state["center"][1] + motion["semi_major"] * math.cos(theta) * math.sin(motion["angle"]) + motion["semi_minor"] * math.sin(theta) * math.cos(motion["angle"])\n')
                f.write('                if not set_pose(model_name, x, y, state["z"]):\n')
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
                f.write('                    exit(1)\n')
                # Use linear_dt (smallest interval) so all motion types stay responsive
                f.write('        time.sleep(linear_dt)\n')
                f.write('    except KeyboardInterrupt:\n')
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

            env = os.environ.copy()
            env['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
            self.script_process = subprocess.Popen(['python3', script_path], env=env)

        # Only purge models that were successfully removed from Gazebo
        self.models = [m for m in self.models
                       if not (m["status"] == "removed" and m["name"] in applied_names)]
        # Only clear status for models that were actually pushed to Gazebo;
        # failed models keep their current status so they can be retried.
        for model in self.models:
            if model["name"] in applied_names:
                model["status"] = ""

        n_ok = len(applied_names)
        n_err = len(errors)
        print(f"[DWG] apply_changes done — {n_ok} applied, {n_err} failed")
        return errors

    def cleanup(self):
        if self.sdf_tree and self.world_path:
            try:
                self.save_sdf(self.world_path)
            except Exception:
                pass

        if self.script_process and self.script_process.poll() is None:
            try:
                self.script_process.send_signal(signal.SIGINT)
                self.script_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.script_process.terminate()
                try:
                    self.script_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.script_process.kill()
                    self.script_process.wait(timeout=2)
            except Exception:
                pass
            self.script_process = None

        if self.process and self.process.poll() is None:
            try:
                self.process.send_signal(signal.SIGINT)
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=2)
            except Exception:
                pass
            self.process = None

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

        static_str = "false" if "motion" in props else "true"
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
        if static_str != "true":
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
            sdf += f"""<inertial>
                <mass>{mass:.6f}</mass>
                <inertia>
                    <ixx>{ixx:.6f}</ixx><ixy>0</ixy><ixz>0</ixz>
                    <iyy>{iyy:.6f}</iyy><iyz>0</iyz>
                    <izz>{izz:.6f}</izz>
                </inertia>
            </inertial>"""
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
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.sdf_tree.write(path, encoding="utf-8", xml_declaration=True)
