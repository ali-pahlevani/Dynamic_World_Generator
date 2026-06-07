#!/bin/bash
gz sim /home/alip/Dynamic_World_Generator/worlds/gazebo/harmonic/test_world.sdf &
sleep 2
python3 /home/alip/Dynamic_World_Generator/worlds/gazebo/harmonic/move_code/test_world_moveObstacles.py &
wait
