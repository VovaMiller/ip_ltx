import pytest

from ip_ltx.misc.task_manager import TaskManager


def test_size_all():
    tm = TaskManager()
    assert len(tm) == 148

def test_tasks_existence():
    tm = TaskManager()

    # existent (generic)
    assert "tm_eliminate_camp_1" in tm
    assert "dolg_defend_lager_1" in tm
    assert "hunter_eliminate_lager" in tm

    # existent (stotyline)
    assert "tutorial_find_artefact" in tm
    assert "mil_mad_job" in tm
    assert "sar_monolith" in tm

    # non-existent
    assert "tm_find_artefact" not in tm
    assert "tm_find_artefact_5" not in tm
    assert "tm_find_artefact_10" not in tm

def test_task_data_1():
    tm = TaskManager()
    task = tm["tm_defend_camp_1"]
    assert task._id == "tm_defend_camp_1"
    assert task._type == "defend_lager"

def test_task_data_2():
    tm = TaskManager()
    task = tm["sar_secret_lab"]
    assert task._id == "sar_secret_lab"
    assert task._type == "storyline"

def test_task_data_3():
    tm = TaskManager()
    with pytest.raises(KeyError):
        _ = tm["freedom_defend_lager_3"]

def test_generic_task_data_1():
    tm = TaskManager()
    task = tm.generic_task("dolg_find_item_1")
    assert task._id == "dolg_find_item_1"
    assert task._type == "find_item"
    assert task.text == "dolg_find_item_1_text"
    assert task.article == "dolg_find_item_1_descr"
    assert task.parent == "dolg"
    assert task.target == "wpn_lr300_m1"
    assert task.count is None

def test_generic_task_data_2():
    tm = TaskManager()
    with pytest.raises(ValueError):
        _ = tm.generic_task("tutorial_find_artefact")

def test_generic_task_data_3():
    tm = TaskManager()
    with pytest.raises(KeyError):
        _ = tm.generic_task("tm_kill_yourself")

def test_generic_tasks_size_all():
    tm = TaskManager()
    assert len(list(tm.generic_tasks())) == 91

def test_generic_tasks_size_subset():
    tm = TaskManager()
    task_ids = [
        "tm_eliminate_camp_1",
        "barmen_find_artefact_2",
        "ecolog_monster_part_3",
        "dolg_eliminate_lager_4",
        "freedom_kill_stalker_5",
        "zastava_commander_eliminate_lager",
        "drunk_dolg_find_item",
    ]
    assert len(list(tm.generic_tasks(task_ids))) == len(task_ids)

def test_generic_tasks_data_1():
    tm = TaskManager()
    task_ids = [
        "tm_eliminate_camp_1",
        "barmen_find_artefact_2",
        "ecolog_monster_part_3",
        "freedom_kill_stalker_5",
        "drunk_dolg_find_item",
    ]
    tasks = {task._id: task for task in tm.generic_tasks(task_ids)}
    assert tasks["tm_eliminate_camp_1"]._type == "eliminate_lager"
    assert tasks["tm_eliminate_camp_1"].target == "gar_bandit_stroyka"
    assert tasks["barmen_find_artefact_2"]._type == "artefact"
    assert tasks["barmen_find_artefact_2"].target == "af_rusty_kristall"
    assert tasks["ecolog_monster_part_3"]._type == "monster_part"
    assert tasks["ecolog_monster_part_3"].target == "mutant_boar_leg"
    assert tasks["freedom_kill_stalker_5"]._type == "kill_stalker"
    assert tasks["freedom_kill_stalker_5"].target == "sim_dolg_master"
    assert tasks["drunk_dolg_find_item"]._type == "find_item"
    assert tasks["drunk_dolg_find_item"].target == "wpn_abakan_m2"

def test_generic_tasks_data_2():
    """Attempt to also obtain storyline task."""
    tm = TaskManager()
    task_ids = [
        "tm_eliminate_camp_1",
        "garbage_meet_stalker",
        "barmen_find_artefact_2",
    ]
    with pytest.raises(ValueError):
        _ = list(tm.generic_tasks(task_ids))

def test_generic_tasks_data_3():
    """Attempt to also obtain non-existent task."""
    tm = TaskManager()
    task_ids = [
        "tm_eliminate_camp_1",
        "garbage_task",
        "barmen_find_artefact_2",
    ]
    with pytest.raises(KeyError):
        _ = list(tm.generic_tasks(task_ids))
