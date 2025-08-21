# Dynamic World Generator Wizard

![Dynamic World Generator Wizard Banner](path/to/banner.png)

**Dynamic World Generator Wizard** is a *PyQt5*-based graphical user interface (*GUI*) application designed to create and manage dynamic simulation worlds for *Gazebo* (*Harmonic* or *Fortress* versions). It allows users to build custom worlds with walls, static obstacles (boxes, cylinders, spheres), and dynamic obstacles with various motion paths (linear, elliptical, polygon). The tool generates *SDF* (*Simulation Description Format*) files for *Gazebo* and includes a motion script to animate dynamic obstacles. This app is ideal for robotics simulation, testing autonomous systems, or educational purposes in simulation environments.

The wizard guides users through a step-by-step process, ensuring an intuitive experience. It supports creating new worlds from empty templates, loading existing ones, and applying changes in real-time to *Gazebo*.

## Key Features

* **Simulation Selection**: Choose *Gazebo Harmonic* (recommended) or *Fortress*. *Isaac Sim* support is under development.
* **Wall Design**: Draw walls on a canvas with customizable width, height, and color.
* **Static Obstacles**: Add boxes, cylinders, or spheres with dimensions and colors.
* **Dynamic Obstacles**: Assign motion paths (linear, elliptical, polygon) with velocity and randomness (*std*).
* **Preview and Apply**: Real-time canvas preview and apply changes to *Gazebo* simulation.
* **Coming Soon**: Teasers for future features like *Gazebo Ionic* and *Isaac Sim 4.5.0/5.0.0*.

![Simulation Selection Page Screenshot](path/to/simulation_selection_screenshot.png)

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

![Code Structure Diagram](path/to/code_structure_diagram.png)

## Installation and Usage

### Prerequisites

* **Python**: *3.10+* (tested on *3.10*).
* **Dependencies**: Install required libraries:
  ```bash
  pip install PyQt5 lxml
  ```
* **Gazebo**: Install *Gazebo Harmonic* (recommended) or *Fortress*:
  * For *Harmonic* (*Ubuntu*/*Debian*):
    ```bash
    sudo apt-get install gz-harmonic
    ```
  * For *Fortress*:
    ```bash
    sudo apt-get install gz-fortress
    ```
  * For *Harmonic*, also install transport libraries:
    ```bash
    pip install gz-transport13 gz-msgs10
    ```
* **Images and Worlds**: Ensure the `images/intro/`, `images/future/`, and `worlds/gazebo/{version}/empty_world.sdf` directories exist in the project root. Copy sample files or create placeholders if needed.

### Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/dynamic-world-generator.git
   cd dynamic-world-generator
   ```

2. **Create `__init__.py` Files** (if missing):
   ```bash
   touch code/__init__.py
   touch code/classes/__init__.py
   touch code/classes/pages/__init__.py
   touch code/utils/__init__.py
   ```

3. **Verify Directory Structure**:
   Ensure the following exist or create them:
   ```bash
   mkdir -p images/intro images/future worlds/gazebo/harmonic worlds/gazebo/fortress
   ```

4. **Create Empty World Template** (if missing):
   Create `empty_world.sdf` in `worlds/gazebo/harmonic/` and `worlds/gazebo/fortress/`:
   ```xml
   <sdf version='1.9'>
     <world name='empty'>
       <physics name='default_physics' type='ode' />
       <light name='sun' type='directional' />
       <scene>
         <ambient>0.4 0.4 0.4</ambient>
         <background>0.7 0.7 0.7</background>
       </scene>
     </world>
   </sdf>
   ```
   Adjust `version='1.8'` for *Fortress*.

5. **Run the Application**:
   From the project root:
   ```bash
   python3 -m code.dwg_wizard
   ```
   Alternatively, from the `code/` directory (if path issues occur, add `sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))` to `dwg_wizard.py`):
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
* **Missing SDF Files**: Ensure `empty_world.sdf` exists in `worlds/gazebo/{version}/`. Use the template above if absent.
* **Path Issues**: If images or worlds are not found, verify paths in `code/utils/config.py`. Update `PROJECT_ROOT` if the project is moved.
* **Transport Errors (Harmonic)**: Ensure `gz-transport13` and `gz-msgs10` are installed for dynamic obstacle motion scripts.

![Installation Troubleshooting Screenshot](path/to/installation_troubleshooting_screenshot.png)

## Tutorial: Creating a Complete Dynamic World

The wizard guides you through a step-by-step process to build a dynamic world. Below is a detailed tutorial covering all options and features.

### Step 1: Welcome Page

* The app opens with a welcome screen displaying the title **Dynamic World Generator Wizard** and an animated *GIF* (*1200x750*).
* No configuration is needed; click *Next* to proceed.

![Welcome Page Screenshot](path/to/welcome_page_screenshot.png)

### Step 2: Select Simulation Platform

* **Choose Simulation**:
  * **Gazebo Harmonic (Recommended)**: Select for the latest features (image: *290x290* `harmonic.png`).
  * **Gazebo Fortress**: Select for stable, older version (image: *290x290* `fortress.jpeg`).
  * **Isaac Sim**: Under development, currently disabled (image: *550x400* `isaacsim_450_gray.png`).
* Buttons have hover effects (light blue) and styles (blue background, white text, *14pt* font).
* Once a simulation is selected, the page completes, allowing you to click *Next*.

![Simulation Selection Screenshot](path/to/simulation_selection_screenshot.png)

### Step 3: Design Walls

* **Create or Load World**:
  * Enter a world name (e.g., `myWorld`) in the text field.
  * Click *Create New World* to copy `empty_world.sdf` or *Load World* to open an existing *SDF* file.
* **Add Walls**:
  * Set width (*m*, e.g., *0.2*), height (*m*, e.g., *1.5*), and color (*Black*, *Gray*, *White*, *Red*, *Blue*, *Green*).
  * Click on the canvas (grid-snapped, *10px* spacing) twice to draw a wall (start and end points).
  * Walls appear as lines on the canvas.
* **Remove Walls**: Select a wall from the list and click *Remove Selected Wall*.
* **Apply Changes**: Click *Apply and Preview* to update the *Gazebo* simulation and save to the *SDF* file (`worlds/gazebo/{version}/myWorld.sdf`).
* **Canvas Controls**: Zoom with the mouse wheel, pan with the middle mouse button.
* Click *Next* when done.

![Walls Design Screenshot](path/to/walls_design_screenshot.png)

### Step 4: Add Static Obstacles

* **Select Obstacle Type**:
  * **Box**: Set width, length, height (*m*).
  * **Cylinder**: Set radius, height (*m*).
  * **Sphere**: Set radius (*m*).
* **Customize**:
  * Choose color (*Black*, *Gray*, *White*, *Red*, *Blue*, *Green*).
  * Enter dimensions (e.g., box: *1x1x1*; cylinder: radius=*0.5*, height=*1*).
* **Add Obstacles**: Click on the canvas (grid-snapped) to place the obstacle at the desired position.
* **Remove Obstacles**: Select from the list and click *Remove Selected Obstacle*.
* **Apply Changes**: Click *Apply and Preview* to update *Gazebo* and *SDF*.
* **Canvas Controls**: Zoom/pan as before.
* Click *Next* when done.

![Static Obstacles Screenshot](path/to/static_obstacles_screenshot.png)

### Step 5: Add Dynamic Obstacles

* **Select Obstacle**: Choose a static obstacle from the list (populated from Step 4).
* **Choose Motion Type**:
  * **Linear**: Define a path with *2* points (red line).
  * **Elliptical**: Define a center point and semi-major/minor axes (green ellipse).
  * **Polygon**: Define multiple points, close with *Finish Path* (blue lines).
* **Customize Motion**:
  * Set velocity (*m/s*, e.g., *5.0*) and *std* (randomness, e.g., *0.1*).
  * For elliptical, set semi-major (e.g., *2.0*) and semi-minor (e.g., *1.0*) axes.
* **Define Path**:
  * Click *Start Defining Path*.
  * Click on the canvas (grid-snapped) to add points:
    * Linear: *2* clicks.
    * Elliptical: *1* click (defines orientation).
    * Polygon: Multiple clicks, then *Finish Path* to close.
  * Path appears on the canvas for preview.
* **Apply Changes**: Click *Apply and Preview* to update the *SDF* and generate a motion script (`worlds/gazebo/{version}/move_code/myWorld_moveObstacles.py`) that animates obstacles in *Gazebo*.
* **Canvas Controls**: Zoom/pan as before.
* Click *Next* when done.

![Dynamic Obstacles Screenshot](path/to/dynamic_obstacles_screenshot.png)

### Step 6: Coming Soon Page

* Displays teasers for future features:
  * **Gazebo Ionic**: Upcoming *Gazebo* version (image: *350x350* `ionic.png`).
  * **Isaac Sim 4.5.0/5.0.0**: Future simulator support (images: *350x350* `isaacsim_450.png`, `isaacsim_500.png`).
* Labels are bold, italic, red, *18pt* font, centered below images.
* Click *Finish* to exit the wizard.

![Coming Soon Screenshot](path/to/coming_soon_screenshot.png)

### Full Example: Building a Dynamic World

1. **Launch**: Run `python3 -m code.dwg_wizard`.
2. **Welcome**: Click *Next*.
3. **Select Simulation**: Choose *Gazebo Harmonic*, click *Next*.
4. **Design Walls**:
   * Enter `myWorld`, click *Create New World*.
   * Set width=*0.2*, height=*1.5*, color=*Red*.
   * Draw *4* walls to form a rectangular room (e.g., points at *(-5,5)*, *(5,5)*, *(5,-5)*, *(-5,-5)*).
   * Click *Apply and Preview* to see walls in *Gazebo*.
   * Click *Next*.
5. **Add Static Obstacles**:
   * Select *Box*, set width=*1*, length=*1*, height=*1*, color=*Blue*.
   * Click on canvas to add *3* boxes (e.g., at *(0,0)*, *(2,2)*, *(-2,-2)*).
   * Click *Apply and Preview*.
   * Click *Next*.
6. **Add Dynamic Obstacles**:
   * Select a box (e.g., `Box_1`).
   * Choose *Linear*, velocity=*5.0*, *std*=*0.1*.
   * Click *Start Defining Path*, add *2* points (e.g., *(-3,0)* to *(3,0)*).
   * Click *Apply and Preview* to see motion in *Gazebo*.
   * Repeat for another box with *Elliptical* (semi-major=*2.0*, semi-minor=*1.0*, point at *(2,0)*) and *Polygon* (*3+* points, e.g., *(0,0)*, *(1,1)*, *(-1,1)*).
   * Click *Next*.
7. **Coming Soon**: View features, click *Finish*.

The *SDF* file is saved to `worlds/gazebo/harmonic/myWorld.sdf`, and the motion script runs automatically in *Gazebo*, animating dynamic obstacles.

![Dynamic World Example Screenshot](path/to/dynamic_world_example_screenshot.png)

## Future Visions

**Dynamic World Generator Wizard** is a foundation for an open-source simulation world builder. Planned enhancements include:

* **Isaac Sim Support**: Full integration with *Isaac Sim 4.5.0* and *5.0.0* for advanced simulations.
* **Additional Motion Types**: Sinusoidal, random walk, or spline-based paths.
* **Sensor Integration**: Add cameras, *LIDAR*, or other sensors to models.
* **Export Options**: Support for *ROS2*, *Unity*, or other simulators.
* **UI Enhancements**: Undo/redo, *3D* preview, and drag-and-drop placement.
* **Performance Optimizations**: Faster *SDF* generation and real-time updates.

I’d **love collaborations**! Contribute via pull requests on *GitHub* for bug fixes, new features, or documentation improvements. Reach out via *GitHub Issues* for questions, suggestions, or partnership ideas.

![Future Vision Screenshot](path/to/future_vision_screenshot.png)

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

Please include tests and documentation updates. For major changes, discuss in a *GitHub Issue* first.

## License

This project is licensed under the *MIT License*. See the [LICENSE](LICENSE) file for details.