#!/bin/bash
. ./_settings/setup.sh

# input: id заданий из task_manager.ltx
python "${IP_LTX_DIR}"/generator_task_manager.py \
    frm09e \

read -n 1 -s -r -p "Press any key to close..."
