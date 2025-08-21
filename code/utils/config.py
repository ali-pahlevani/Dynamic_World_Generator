import os

# Project root is the directory containing the 'code' folder
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
INTRO_IMAGES_DIR = os.path.join(IMAGES_DIR, "intro")
FUTURE_IMAGES_DIR = os.path.join(IMAGES_DIR, "future")

WORLDS_DIR = os.path.join(PROJECT_ROOT, "worlds")
WORLDS_GAZEBO_DIR = os.path.join(WORLDS_DIR, "gazebo")