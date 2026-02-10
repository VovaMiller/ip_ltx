#!/bin/bash

IP_LTX_DIR="C:\\iP\\Vova\\prog\\ip_tools\\ip_ltx\\src\\ip_ltx"
export IP_LTX_DIR="$(realpath "${IP_LTX_DIR}" | cygpath -u -f -)"

SETUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
export META_FILEPATH="${SETUP_DIR}/meta.ltx"
