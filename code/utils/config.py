import os

# Project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Directory for images
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
INTRO_IMAGES_DIR = os.path.join(IMAGES_DIR, "intro")
FUTURE_IMAGES_DIR = os.path.join(IMAGES_DIR, "future")

# Directory for Gazebo worlds
WORLDS_DIR = os.path.join(PROJECT_ROOT, "worlds")
WORLDS_GAZEBO_DIR = os.path.join(WORLDS_DIR, "gazebo")