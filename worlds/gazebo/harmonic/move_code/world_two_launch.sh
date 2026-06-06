#!/bin/bash
gz sim /home/alip/Dynamic_World_Generator/worlds/gazebo/harmonic/world_two.sdf &
sleep 2
python3 /home/alip/Dynamic_World_Generator/worlds/gazebo/harmonic/move_code/world_two_moveObstacles.py &
wait
