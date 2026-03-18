import os
import pytest
from pathlib import Path
# from unittest import mock

# @pytest.fixture(scope="session", autouse=True)
# def setup():
#     META_FILEPATH = str(Path(__file__).parent.joinpath("meta-vanilla.ltx").resolve())
#     with mock.patch.dict(os.environ, {"META_FILEPATH": META_FILEPATH}):
#         yield

def pytest_sessionstart(session):
    META_FILEPATH = str(Path(__file__).parent.joinpath("meta-vanilla.ltx").resolve())
    os.environ["META_FILEPATH"] = META_FILEPATH
