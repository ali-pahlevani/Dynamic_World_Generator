# Dynamic World Generator Wizard (V1)

![Dynamic World Generator Wizard Banner](https://github.com/user-attachments/assets/1b00aa22-24d7-40f1-8526-a3612bd7f503)

**Dynamic World Generator Wizard** is a *PyQt5*-based graphical user interface (*GUI*) application designed to create and manage dynamic simulation worlds for *Gazebo* (*Harmonic* or *Fortress* versions). It allows users to build custom worlds with walls, static obstacles (boxes, cylinders, spheres), and dynamic obstacles with various motion paths (linear, elliptical, polygon). The tool generates *SDF* (*Simulation Description Format*) files for *Gazebo* and includes a motion script to animate dynamic obstacles. This app is ideal for robotics simulation, testing autonomous systems, or educational purposes in simulation environments.

The wizard guides users through a step-by-step process, ensuring an intuitive experience. It supports creating new worlds from empty templates, loading existing ones, and applying changes in real-time to *Gazebo*.

## Key Features

* **Simulation Selection**: Choose *Gazebo Harmonic* (recommended) or *Fortress*. *Isaac Sim* support is under development.
* **Wall Design**: Draw walls on a canvas with customizable width, height, and color.
* **Static Obstacles**: Add boxes, cylinders, or spheres with dimensions and colors.
* **Dynamic Obstacles**: Assign motion paths (linear, elliptical, polygon) with velocity and randomness (*std*).
* **Preview and Apply**: Real-time canvas preview and apply changes to *Gazebo* simulation.
* **Coming Soon**: Teasers for future features like *Gazebo Ionic* and *Isaac Sim 4.5.0/5.0.0*.

## Code Structure

The codebase is organized in a modular structure for maintainability, with classes separated by functionality. Here's the directory layout:

```
Dynamic_World_Generator/
├── code/
│   ├── __init__.py
│   ├── classes/
│   │   ├── dynamic_world_wizard.py  # Main wizard class handling navigation and canvas
│   │   ├── zoomable_graphics_view.py  # Custom graphics view for zooming and panning the canvas
│   │   ├── world_manager.py  # Handles world creation, loading, model management, and SDF generation
│   │   ├── pages/
│   │   │   ├── welcome_page.py  # Welcome page with title and GIF
│   │   │   ├── sim_selection_page.py  # Simulation platform selection page
│   │   │   ├── walls_design_page.py  # Wall design page with canvas drawing
│   │   │   ├── static_obstacles_page.py  # Static obstacles addition page
│   │   │   ├── dynamic_obstacles_page.py  # Dynamic obstacles and motion paths page
│   │   │   └── coming_soon_page.py  # Coming soon features page
│   ├── utils/
│   │   ├── config.py  # Directory constants for images and worlds
│   │   └── color_utils.py  # Utility for color mapping
│   └── dwg_wizard.py  # Entry point to run the application
├── images/
│   ├── intro/
│   │   ├── harmonic.png
│   │   ├── fortress.jpeg
│   │   └── isaacsim_450_gray.png
│   └── future/
│       ├── ionic.png
│       ├── isaacsim_450.png
│       └── isaacsim_500.png
├── worlds/
│   └── gazebo/
│       ├── harmonic/
│       │   ├── move_code # Motion scripts to animate dynamic obstacles (separate .py file + bash launcher file)
│       │   └── empty_world.sdf
│       └── fortress/
│           ├── move_code # Motion scripts to animate dynamic obstacles (separate .py file + bash launcher file)
│           └── empty_world.sdf
└── README.md
```

* **`code/classes/`**: Contains core classes, including the wizard and page-specific logic.
* **`code/classes/pages/`**: Individual wizard pages for modular *UI* components.
* **`code/utils/`**: Shared utilities like path constants and color functions.
* **`code/dwg_wizard.py`**: The main script to launch the wizard.
* **`images/`**: Stores images for *UI* (intro and future features).
* **`worlds/`**: Stores *Gazebo* world files and generated motion scripts.

## Installation and Usage

### Prerequisites

* **Python**: *3.10+* (tested on *3.10*).
* **Dependencies**: Install required libraries:
  ```bash
  pip install PyQt5 lxml
  ```
* **Gazebo**: Install *Gazebo Harmonic* (recommended) or *Fortress*:
  * For *Harmonic* (*Ubuntu*/*Debian*), please visit:
    [https://gazebosim.org/docs/harmonic/install_ubuntu/](https://gazebosim.org/docs/harmonic/install_ubuntu/)

  * For *Fortress*, please visit:
    [https://gazebosim.org/docs/fortress/install_ubuntu/](https://gazebosim.org/docs/fortress/install_ubuntu/)

  * For *Harmonic*, also install transport libraries:
    ```bash
    pip install gz-transport13 gz-msgs10
    ```
* **Images and Worlds**: Ensure the `images/intro/`, `images/future/`, and `worlds/gazebo/{version}/empty_world.sdf` directories exist in the project root.

### Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ali-pahlevani/dynamic-world-generator.git
   cd dynamic-world-generator
   ```

2. **Run the Application**:
   Run the main file from the `code/` directory:
   ```bash
   cd code
   python3 dwg_wizard.py
   ```

### Troubleshooting Installation

* **PyQt5 Errors**: Ensure a display server is running (e.g., on *WSL*, use `export DISPLAY=:0` or install an *X server* like *Xming*).
* **Gazebo Not Found**: Verify installation:
  ```bash
  gz sim --version  # For Harmonic
  ign gazebo --version  # For Fortress
  ```
* **Missing SDF Files**: Ensure `empty_world.sdf` exists in `worlds/gazebo/{version}/`.
* **Path Issues**: If images or worlds are not found, verify paths in `code/utils/config.py`. Update `PROJECT_ROOT` if the project is moved.
* **Transport Errors (Harmonic)**: Ensure `gz-transport13` and `gz-msgs10` are installed for dynamic obstacle motion scripts.

## Tutorial: Creating a Complete Dynamic World

The wizard guides you through a step-by-step process to build a dynamic world. Below is a detailed tutorial covering all options and features.

### Step 1: Welcome Page

<img width="1857" height="1048" alt="Welcome Page" src="https://github.com/user-attachments/assets/7bbd4df6-e7d6-4bad-8743-cbef0037cfc5" />

### Step 2: Select Simulation Platform

* **Choose Simulation**:
  * **Gazebo Harmonic (Recommended)**: Select for the latest features. Recommended for the best outcome and results.
  * **Gazebo Fortress**: Not suitable for dynamic motions (since uses *subprocess* instead of *python bindings*). You could use it mainly for building a static world.
  * **Isaac Sim**: Under development, currently disabled.
  * Click *Next* when done.

<img width="1857" height="1048" alt="Simulation Selection" src="https://github.com/user-attachments/assets/7d7aa432-506c-49c9-9ad2-50e3b1d29ad7" />

### Step 3: Design Walls

* **Create or Load World**:
  * Enter a world name (e.g., `myWorld`) in the text field.
  * Click *Create New World* to copy `empty_world.sdf` or *Load World* to open an existing *SDF* file.
* **Add Walls**:
  * Set width (*m*, e.g., *0.2*), height (*m*, e.g., *1.5*), and color (*Black*, *Gray*, *White*, *Red*, *Blue*, *Green*).
  * Click on the canvas twice to draw a wall (start and end points).
  * Walls appear as lines on the canvas.
* **Remove Walls**: Select a wall from the list and click *Remove Selected Wall*.
* **Apply Changes**: Click *Apply and Preview* to update the *Gazebo* simulation and save to the *SDF* file (`worlds/gazebo/{version}/myWorld.sdf`).
* **Canvas Controls**: Zoom with the mouse wheel, pan with the middle mouse button.
* Click *Next* when done.

<img width="1857" height="1048" alt="Walls Design" src="https://github.com/user-attachments/assets/522a2955-2ce6-49a9-a17e-8fd4d751ad32" />

### Step 4: Add Static Obstacles

* **Select Obstacle Type**:
  * **Box**: Set width, length, height (*m*).
  * **Cylinder**: Set radius, height (*m*).
  * **Sphere**: Set radius (*m*).
* **Customize**:
  * Choose color (*Black*, *Gray*, *White*, *Red*, *Blue*, *Green*).
  * Enter dimensions (e.g., box: *1x1x1*; cylinder: radius=*0.5*, height=*1*).
* **Add Obstacles**: Click on the canvas to place the obstacle at the desired position.
* **Remove Obstacles**: Select from the list and click *Remove Selected Obstacle*.
* **Apply Changes**: Click *Apply and Preview* to update *Gazebo* and *SDF*.
* **Canvas Controls**: Zoom/pan as before.
* Click *Next* when done.

<img width="1857" height="1048" alt="Static Obstacles" src="https://github.com/user-attachments/assets/2f1c0359-c13b-42ad-8213-d121789d3b4f" />

### Step 5: Add Dynamic Obstacles

* **Select Obstacle**: Choose a static obstacle from the list (populated from Step 4).
* **Choose Motion Type**:
  * **Linear**: Define a path with *2* points (red line).
  * **Elliptical**: Define a point to act as a guider. The direction of the semi-major axis of the ellipse will be along the line connecting the defined point and the center of the obstacle (green ellipse).
  * **Polygon**: Define multiple points, close with *Finish Path* (blue lines).
* **Customize Motion**:
  * Set velocity (*m/s*, e.g., *5.0*) and *std* (randomness, e.g., *0.1*).
  * For elliptical, set semi-major (e.g., *2.0*) and semi-minor (e.g., *1.0*) axes.
* **Define Path**:
  * Click *Start Defining Path*.
  * Click on the canvas to add points:
    * Linear: *2* clicks.
    * Elliptical: *1* click (defines orientation).
    * Polygon: Multiple clicks, then *Finish Path* to close.
  * Path appears on the canvas for preview.
* **Apply Changes**: Click *Apply and Preview* to update the *SDF* and generate a motion script (`worlds/gazebo/{version}/move_code/myWorld_moveObstacles.py`) that animates obstacles in *Gazebo*.
* **Canvas Controls**: Zoom/pan as before.
* Click *Next* when done.

<img width="1857" height="1048" alt="Dynamic Obstacles" src="https://github.com/user-attachments/assets/b287e0b4-e7d1-41d3-8f04-daedb002bf95" />

### Step 6: Coming Soon Page

* Displays teasers for future features:
  * **Gazebo Ionic**: Upcoming *Gazebo* version.
  * **Isaac Sim 4.5.0/5.0.0**: Future simulator support.
* Click *Finish* to exit the wizard.

<img width="1857" height="1048" alt="Coming Soon" src="https://github.com/user-attachments/assets/56a646ee-42cc-4d98-b168-8dd1ad0e1214" />

## Future Visions

**Dynamic World Generator Wizard** is a foundation for an open-source simulation world builder. Planned enhancements include:

* **Isaac Sim Support**: Full integration with *Isaac Sim 4.5.0* and *5.0.0* for advanced simulations.
* **Additional Motion Types**: Sinusoidal, random walk, or spline-based paths.
* **Export Options**: Support for *ROS2*, *Unity*, or other simulators.
* **UI Enhancements**: Undo/redo, *3D* preview, and drag-and-drop placement.
* **Performance Optimizations**: Faster *SDF* generation and real-time updates.
* **And definitely a lot more!!!**

I’d **love collaborations**! Contribute via pull requests on *GitHub* for bug fixes, new features, or documentation improvements. Reach out via *GitHub Issues* for questions, suggestions, or partnership ideas.

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

Please include tests and documentation updates. For major changes, discuss in a *GitHub Issue* first.

---

+ If you have any questions, please let me know: **a.pahlevani1998@gmail.com**

+ Also, don't forget to check out our **website** at: **https://www.SLAMbotics.org**
