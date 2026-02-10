#!/bin/bash
. ./_settings/setup.sh
python "${IP_LTX_DIR}"/analyzer_spawn.py
read -n 1 -s -r -p "Press any key to close..."
