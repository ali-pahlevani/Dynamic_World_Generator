# Dynamic World Generator Wizard (V2)

![Dynamic World Generator Wizard Banner](https://github.com/user-attachments/assets/1b00aa22-24d7-40f1-8526-a3612bd7f503)

**Dynamic World Generator Wizard** is a *PyQt5*-based graphical wizard application for building and managing dynamic simulation worlds. V2 adds full **Gazebo Ionic** support, a **Map Generation** step that exports a *ROS 2*-compatible occupancy grid map (`.pgm` + `.yaml`) directly from the designed world, and a fully responsive UI that adapts to any window size.

The wizard supports *Gazebo Ionic*, *Harmonic*, and *Fortress*. It guides users through a step-by-step process: select a simulator, design walls, place static and dynamic obstacles, generate an occupancy map, and apply everything to a live *Gazebo* session — all from one window.

🙏 A special thanks to **Professor Sousso KELOUWANI** for his excellent idea that inspired the creation of this application.

## What's New in V2

* **Gazebo Ionic Support**: Full support for *Gazebo Ionic* alongside *Harmonic* and *Fortress*, including the correct *SDF 1.12* world template, `gz-transport14` / `gz-msgs11` Python bindings for dynamic obstacles, and dedicated world and map output directories.
* **Map Generation**: Export a *ROS 2*-ready occupancy grid (`.pgm` + `.yaml`) from the finished world, with configurable resolution, origin, thresholds, and mode.
* **Fully Responsive UI**: Sidebar, cards, buttons, and input labels all adapt as the window resizes — no truncation or overlap at any size.
* **Improved Navigation**: Centered, word-wrapped nav labels with a wider sidebar and larger font for readability.
* **Root Launcher**: Run the app with `./dwg_wizard` from the repo root — no need to `cd code/` manually.

## Key Features

* **Simulation Selection**: Choose *Gazebo Ionic*, *Harmonic* (recommended), or *Fortress*. *Isaac Sim* support is under development.
* **Wall Design**: Draw walls on an interactive canvas with customizable width, height, and color.
* **Static Obstacles**: Place boxes, cylinders, or spheres with per-type dimension controls.
* **Dynamic Obstacles**: Assign linear, elliptical, or polygon motion paths with velocity and randomness (*std*).
* **Map Generation**: Render an occupancy grid map from all static geometry, export as `.pgm` + `.yaml` ready for *ROS 2 Nav2*.
* **Preview and Apply**: Real-time canvas preview; apply changes to *Gazebo* in one click.
* **Coming Soon**: *Isaac Sim 4.5.0*, *5.0.0*, and *5.1.0* support.

## Code Structure

```
Dynamic_World_Generator/
├── dwg_wizard                         # Root launcher — run from repo root
├── code/
│   ├── __init__.py
│   ├── classes/
│   │   ├── dynamic_world_wizard.py    # Main wizard: navigation sidebar, canvas sharing, stylesheet
│   │   ├── zoomable_graphics_view.py  # Canvas with mouse-wheel zoom, middle-button pan, scale label
│   │   ├── world_manager.py           # World creation, loading, model management, SDF generation
│   │   ├── apply_worker.py            # Background thread for applying changes to Gazebo
│   │   ├── responsive_widgets.py      # WrapButton (text wraps when narrow), ButtonRow (stacks when narrow)
│   │   └── pages/
│   │       ├── welcome_page.py        # Welcome page with responsive animated GIF and title
│   │       ├── sim_selection_page.py  # Simulation platform selection with responsive image cards
│   │       ├── walls_design_page.py   # Wall design page with canvas drawing
│   │       ├── static_obstacles_page.py   # Static obstacle placement
│   │       ├── dynamic_obstacles_page.py  # Dynamic obstacle motion paths
│   │       ├── map_generation_page.py     # Occupancy map generation and export
│   │       └── coming_soon_page.py        # Future features teaser
│   ├── utils/
│   │   ├── config.py                  # Directory constants (images, worlds, maps)
│   │   └── color_utils.py             # Color-name to RGB mapping
│   └── dwg_wizard.py                  # Entry point
├── images/
│   ├── intro/                         # Images shown on the simulation selection page
│   │   ├── welcome.gif
│   │   ├── ionic.png
│   │   ├── harmonic.png
│   │   └── fortress.jpeg
│   └── future/                        # Images shown on the Coming Soon page
│       ├── isaacsim_450.png
│       ├── isaacsim_500.png
│       └── isaacsim_510.png
├── worlds/
│   ├── gazebo/
│   │   ├── ionic/
│   │   │   ├── empty_world.sdf        # Template (SDF 1.12, tracked); generated worlds are git-ignored
│   │   │   └── move_code/             # Generated launch + motion scripts (git-ignored)
│   │   ├── harmonic/
│   │   │   ├── empty_world.sdf        # Template (SDF 1.9, tracked)
│   │   │   └── move_code/
│   │   └── fortress/
│   │       ├── empty_world.sdf        # Template (SDF 1.8, tracked)
│   │       └── move_code/
│   └── isaacsim/
│       ├── 450/
│       ├── 500/
│       └── 510/
├── maps/
│   ├── gazebo/
│   │   ├── ionic/                     # Generated maps land here (git-ignored)
│   │   ├── harmonic/
│   │   └── fortress/
│   └── isaacsim/
│       ├── 450/
│       ├── 500/
│       └── 510/
└── README.md
```

> **Note**: Generated world `.sdf` files, launch scripts (`*_launch.sh`), motion scripts (`*_moveObstacles.py`), and map outputs (`.pgm`, `.yaml`) are all listed in `.gitignore`. Only the `empty_world.sdf` templates are tracked.

## Installation and Usage

### Prerequisites

* **Python**: *3.10+* (tested on *3.10*).
* **Python Dependencies**:
  ```bash
  pip install PyQt5 lxml
  ```
* **Gazebo**: Install your preferred version:

  | Version | Install guide |
  |---|---|
  | *Ionic* | [gazebosim.org/docs/ionic/install_ubuntu](https://gazebosim.org/docs/ionic/install_ubuntu/) |
  | *Harmonic* | [gazebosim.org/docs/harmonic/install_ubuntu](https://gazebosim.org/docs/harmonic/install_ubuntu/) |
  | *Fortress* | [gazebosim.org/docs/fortress/install_ubuntu](https://gazebosim.org/docs/fortress/install_ubuntu/) |

* **Python transport bindings** (required for dynamic obstacle motion scripts):

  * *Ionic* — installed via apt (no pip wheel available):
    ```bash
    sudo apt install python3-gz-transport14 python3-gz-msgs11
    ```
  * *Harmonic* — available via pip:
    ```bash
    pip install gz-transport13 gz-msgs10
    ```
  * *Fortress* — no Python bindings needed; motion scripts use subprocess-based service calls instead.

### Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ali-pahlevani/Dynamic_World_Generator.git
   cd Dynamic_World_Generator
   ```

2. **Run the Application** (from the repo root):
   ```bash
   ./dwg_wizard
   ```
   Or, from the `code/` directory directly:
   ```bash
   cd code
   python3 dwg_wizard.py
   ```

### Troubleshooting

* **PyQt5 Errors**: Make sure a display server is running. On *WSL*, set `export DISPLAY=:0` or use an *X server* like *Xming*.
* **Gazebo Not Found**:
  ```bash
  gz sim --version      # Ionic or Harmonic
  ign gazebo --version  # Fortress
  ```
* **Missing SDF Template**: `empty_world.sdf` must exist in `worlds/gazebo/{version}/`.
* **Path Issues**: If images or worlds are not found, check `code/utils/config.py`. Update `PROJECT_ROOT` if the repo was moved.
* **Transport Errors (Ionic)**: Ensure `python3-gz-transport14` and `python3-gz-msgs11` are installed via apt — pip wheels are not available for Ionic bindings.
* **Transport Errors (Harmonic)**: Ensure `gz-transport13` and `gz-msgs10` are installed — they are required to animate dynamic obstacles.

## Tutorial: Building a Complete Dynamic World

The wizard walks you through every step sequentially. Each page can be revisited using the left-hand navigation sidebar.

### Step 1: Welcome

An animated overview of the application. Click *Next* to begin.

<img width="1857" height="1048" alt="Welcome Page" src="https://github.com/user-attachments/assets/7bbd4df6-e7d6-4bad-8743-cbef0037cfc5" />

### Step 2: Select Simulation

Three platforms are available, in this order:

* **Gazebo Ionic**: Latest *Gazebo* release. Full dynamic obstacle support via `gz-transport14` / `gz-msgs11` Python bindings. Uses *SDF 1.12*.
* **Gazebo Harmonic** *(Recommended)*: Stable, widely adopted release. Full dynamic obstacle support via `gz-transport13` / `gz-msgs10`. Uses *SDF 1.9*.
* **Gazebo Fortress**: Suitable primarily for static worlds. Dynamic motion falls back to subprocess-based service calls instead of Python bindings. Uses *SDF 1.8*.

Click the *Select* button on your chosen card, then click *Next*.

<img width="1857" height="1048" alt="Simulation Selection" src="https://github.com/user-attachments/assets/7d7aa432-506c-49c9-9ad2-50e3b1d29ad7" />

### Step 3: Design Walls

* **Create or Load World**: Enter a world name (letters, numbers, underscores only) and click *Create New* or *Load*.
* **Draw Walls**: Set width (*m*), height (*m*), and color, then click twice on the canvas to place a wall (start → end point). Each wall appears as a line on the canvas.
* **Remove Walls**: Select a wall from the list, click *Remove Selected*.
* **Apply**: *Apply and Preview* saves to the *SDF* file and pushes to the live *Gazebo* session.
* **Canvas Controls**: Scroll wheel to zoom, middle mouse button to pan.

<img width="1857" height="1048" alt="Walls Design" src="https://github.com/user-attachments/assets/522a2955-2ce6-49a9-a17e-8fd4d751ad32" />

### Step 4: Static Obstacles

* **Types**: Box (width × length × height), Cylinder (radius × height), Sphere (radius).
* **Placement**: Set dimensions and color, then click the canvas to drop the obstacle at that position.
* **Remove**: Select from the list and click *Remove Selected*.
* **Apply**: *Apply and Preview* updates the *SDF* and *Gazebo*.

<img width="1857" height="1048" alt="Static Obstacles" src="https://github.com/user-attachments/assets/2f1c0359-c13b-42ad-8213-d121789d3b4f" />

### Step 5: Dynamic Obstacles

* **Select Obstacle**: Pick any static obstacle from the list.
* **Motion Type**:
  * **Linear**: Click 2 points → red path line.
  * **Elliptical**: Click 1 point to set the semi-major axis direction → green ellipse preview. Set semi-major and semi-minor axes before clicking.
  * **Polygon**: Click multiple points, then *Finish Path* to close → blue path.
* **Parameters**: Set velocity (*m/s*) and std (randomness).
* **Workflow**: Click *Start Path*, click the canvas to define points, click *Finish Path* (polygon only).
* **Apply**: *Apply and Preview* updates the *SDF* and generates:
  * `worlds/gazebo/{version}/move_code/{world}_moveObstacles.py` — motion script
  * `worlds/gazebo/{version}/move_code/{world}_launch.sh` — launcher for that script

<img width="1857" height="1048" alt="Dynamic Obstacles" src="https://github.com/user-attachments/assets/b287e0b4-e7d1-41d3-8f04-daedb002bf95" />

### Step 6: Map Generation

This step renders all static geometry (walls, boxes, cylinders, spheres) into a *ROS 2*-compatible occupancy grid map.

* **Map Name**: Enter a name (e.g., `my_map`); the image file is named automatically.
* **Map Settings (YAML)**:
  * **Mode**: `trinary` (default), `scale`, or `raw`.
  * **Resolution**: Meters per pixel (e.g., `0.05`).
  * **Origin X / Y**: Bottom-left corner of the map in world coordinates — auto-computed from geometry with 2 m padding.
  * **Negate**, **Occupied threshold**, **Free threshold**: Standard *ROS 2* nav-stack parameters.
* **Live Preview**: The map preview updates automatically as settings change.
* **Generate Map**: Exports to `maps/gazebo/{version}/{map_name}/`:
  * `{map_name}.pgm` — grayscale occupancy image (P5 binary PGM)
  * `{map_name}.yaml` — *ROS 2* map metadata file

### Step 7: Coming Soon

Teasers for planned simulator support:

* **Isaac Sim 4.5.0** *(In Progress)*
* **Isaac Sim 5.0.0** *(Planned)*
* **Isaac Sim 5.1.0** *(Planned)*

Click *Finish* to close the wizard.

<img width="1857" height="1048" alt="Coming Soon" src="https://github.com/user-attachments/assets/56a646ee-42cc-4d98-b168-8dd1ad0e1214" />

## Future Visions

**Dynamic World Generator Wizard** is a foundation for an open-source simulation world builder. Planned enhancements include:

* **Isaac Sim Support**: Full integration with *Isaac Sim 4.5.0*, *5.0.0*, and *5.1.0*.
* **Additional Motion Types**: Sinusoidal, random walk, or spline-based paths.
* **Export Options**: Direct *ROS 2* package export, *Unity*, or other simulator formats.
* **UI Enhancements**: Undo/redo, 3D preview, drag-and-drop obstacle placement.
* **And definitely a lot more!**

I'd **love collaborations**! Contribute via pull requests on *GitHub* for bug fixes, new features, or documentation improvements. Open a *GitHub Issue* for questions, suggestions, or partnership ideas.

## Contributing

1. Fork the repository.
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a pull request.

Please include documentation updates. For major changes, open a *GitHub Issue* first to discuss the approach.

---

+ Questions? Reach out: **a.pahlevani1998@gmail.com**
+ LinkedIn: **https://www.linkedin.com/in/ali-pahlevani/**
