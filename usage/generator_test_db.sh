#!/bin/bash
. ./_settings/setup.sh
python "${IP_LTX_DIR}"/generator_test_db.py
read -n 1 -s -r -p "Press any key to close..."
