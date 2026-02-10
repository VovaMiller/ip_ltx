#!/bin/bash
. ./_settings/setup.sh

# input: names of 2 sections to compare
python "${IP_LTX_DIR}"/analyzer_compare.py \
    "wpn_ak74" \
    "wpn_ak74u" \

read -n 1 -s -r -p "Press any key to close..."
