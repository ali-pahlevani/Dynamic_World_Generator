import os
import subprocess
from xml.etree import ElementTree as ET
from utils.utils import get_color
import math

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
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Up to Dynamic_World_Generator/

    def create_new_world(self, world_name):
        self.world_name = world_name
        empty_world_path = os.path.join(self.base_dir, "worlds", "gazebo", self.version, "empty_world.sdf")
        print(f"Looking for empty world at: {empty_world_path}")  # Debug
        if not os.path.exists(empty_world_path):
            raise FileNotFoundError(f"Empty world file not found: {empty_world_path}")

        if self.version == "fortress":
            cmd = ["ign", "gazebo", empty_world_path]
        else:
            cmd = ["gz", "sim", empty_world_path]
        self.process = subprocess.Popen(cmd)
        self.world_path = os.path.join(self.base_dir, "worlds", "gazebo", self.version, f"{world_name}.sdf")
        print(f"Creating world at: {self.world_path}")  # Debug
        self.models = []
        self.sdf_tree = ET.parse(empty_world_path)
        self.sdf_root = self.sdf_tree.getroot()
        self.world_name = self.sdf_root.find("world").get("name")

    def load_world(self, world_name):
        self.world_name = world_name
        self.world_path = os.path.join(self.base_dir, "worlds", "gazebo", self.version, f"{world_name}.sdf")
        print(f"Loading world at: {self.world_path}")  # Debug
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
        for model in self.sdf_root.findall(".//model"):
            name = model.get("name")
            self.models.append({"name": name, "type": "unknown", "properties": {}, "status": ""})

    def add_model(self, model):
        self.models.append(model)

    def apply_changes(self):
        prefix = "ign" if self.version == "fortress" else "gz"
        for model in self.models:
            # For adding models
            if model["status"] == "new":
                sdf_snippet = self.generate_model_sdf(model)
                cmd = [prefix, "service", "-s", f"/world/{self.world_name}/create",
                    "--reqtype", f"{prefix}.msgs.EntityFactory",
                    "--reptype", f"{prefix}.msgs.Boolean",
                    "--timeout", "3000",
                    "--req", f'sdf: "{sdf_snippet}"']
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise RuntimeError(f"Failed to add model {model['name']}: {result.stderr}")
                model_elem = ET.fromstring(sdf_snippet)
                self.sdf_root.find("world").append(model_elem)

            # For removing models
            elif model["status"] == "removed":
                cmd = [prefix, "service", "-s", f"/world/{self.world_name}/remove",
                    "--reqtype", f"{prefix}.msgs.Entity",
                    "--reptype", f"{prefix}.msgs.Boolean",
                    "--timeout", "3000",
                    "--req", f'name: "{model["name"]}", type: 2']
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise RuntimeError(f"Failed to remove model {model['name']}: {result.stderr}")
                for elem in self.sdf_root.findall(f".//model[@name='{model['name']}']"):
                    self.sdf_root.find("world").remove(elem)

        self.models = [m for m in self.models if m["status"] != "removed"]
        for model in self.models:
            model["status"] = ""
        self.save_sdf(self.world_path)

    def generate_model_sdf(self, model):
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
            pose = f"{center_x} {center_y} {z} 0 0 {yaw}"
            size = (length, props["width"], props["height"])
        else:
            x, y, z = props["position"]
            pose = f"{x} {y} {z} 0 0 0"
            size = props["size"]

        sdf = f"""<model name='{model["name"]}'>
            <pose>{pose}</pose>
            <link name='link'>
                <collision name='collision'>
                    <geometry>"""
        if model_type in ["wall", "box"]:
            width, depth, height = size
            sdf += f"""<box><size>{width} {depth} {height}</size></box>"""
        elif model_type == "cylinder":
            radius, height = size
            sdf += f"""<cylinder><radius>{radius}</radius><length>{height}</length></cylinder>"""
        elif model_type == "sphere":
            radius, = size
            sdf += f"""<sphere><radius>{radius}</radius></sphere>"""
        sdf += f"""</geometry>
                </collision>
                <visual name='visual'>
                    <geometry>"""
        if model_type in ["wall", "box"]:
            width, depth, height = size
            sdf += f"""<box><size>{width} {depth} {height}</size></box>"""
        elif model_type == "cylinder":
            radius, height = size
            sdf += f"""<cylinder><radius>{radius}</radius><length>{height}</length></cylinder>"""
        elif model_type == "sphere":
            radius, = size
            sdf += f"""<sphere><radius>{radius}</radius></sphere>"""
        sdf += f"""</geometry>
                    <material>
                        <diffuse>{color_rgb[0]} {color_rgb[1]} {color_rgb[2]} 1</diffuse>
                    </material>
                </visual>
            </link>
        </model>"""
        return sdf

    def save_sdf(self, path):
        if self.sdf_tree:
            self.sdf_tree.write(path, encoding="utf-8", xml_declaration=True)