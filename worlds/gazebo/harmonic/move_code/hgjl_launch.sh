#!/bin/bash
gz sim /home/alip/Dynamic_World_Generator/worlds/gazebo/harmonic/hgjl.sdf &
sleep 2
python3 /home/alip/Dynamic_World_Generator/worlds/gazebo/harmonic/move_code/hgjl_moveObstacles.py &
wait
