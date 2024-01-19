#!/bin/bash
if pgrep -af "python3 $HOME/bosch_pls/main.py" &>/dev/null; then
    exit
fi
nohup python3 "$HOME/bosch_pls/main.py" > /dev/null
exit