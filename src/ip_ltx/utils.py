import os
import sys

os.system("")  # enables colors for Windows consoles

class ANSI_COLOR_CODE:
    DEF = '\033[0m'
    BLACK   = '\033[90m'  # '\033[30m'
    RED     = '\033[91m'  # '\033[31m'
    GREEN   = '\033[92m'  # '\033[32m'
    YELLOW  = '\033[93m'  # '\033[33m'
    BLUE    = '\033[94m'  # '\033[34m'
    PURPLE  = '\033[95m'  # '\033[35m'
    CYAN    = '\033[96m'  # '\033[36m'
    WHITE   = '\033[97m'  # '\033[37m'

def print_warning(msg, prefix: bool = True, color: bool = True):
    msg_fmt = "{}{}{}{}".format(
        ANSI_COLOR_CODE.YELLOW if color else "",
        "~ " if prefix else "",
        msg,
        ANSI_COLOR_CODE.DEF if color else "",
    )
    print(msg_fmt, file=sys.stderr)

def print_error(msg, prefix: bool = True, color: bool = True):
    msg_fmt = "{}{}{}{}".format(
        ANSI_COLOR_CODE.RED if color else "",
        "! " if prefix else "",
        msg,
        ANSI_COLOR_CODE.DEF if color else "",
    )
    print(msg_fmt, file=sys.stderr)

def cast_safe(val, _type, defval=None):
    try:
        return _type(val)
    except (ValueError, TypeError):
        return defval
