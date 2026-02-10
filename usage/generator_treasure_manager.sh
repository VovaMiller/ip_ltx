#!/bin/bash
. ./_settings/setup.sh

# input: id тайников, уже зарегистрированных в game_story_ids.ltx
python "${IP_LTX_DIR}"/generator_treasure_manager.py \
    mil_ipv30_secret_01 \
    mil_ipv30_secret_02 \
    mil_ipv30_secret_03 \
    mil_ipv30_secret_04 \
    mil_ipv30_secret_05 \
    mil_ipv30_secret_06 \

read -n 1 -s -r -p "Press any key to close..."
