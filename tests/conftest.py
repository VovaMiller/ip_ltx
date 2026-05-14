import os
from pathlib import Path


def pytest_sessionstart():
    meta_filepath = str(Path(__file__).parent.joinpath("meta-vanilla.ltx").resolve())
    os.environ["META_FILEPATH"] = meta_filepath
