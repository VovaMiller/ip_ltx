#!/bin/bash
. ../_settings/setup.sh

python "${IP_LTX_DIR}"/generator_character_desc.py \
    "sample_chrdsc_monolith.txt" \
    "sample_chrdsc_rnd.txt" \
    "sample_chrdsc_test.txt" \

read -n 1 -s -r -p "Press any key to close..."
