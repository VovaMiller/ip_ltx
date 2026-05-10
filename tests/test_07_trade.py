import inspect

import pytest

from ip_ltx import Ini
from ip_ltx.misc.trade import TradeBuy, TradeBuyImpl

# ----------------------------------------------------------------

@pytest.fixture(scope="module")
def trade_sample():
    ini_trade = Ini("trade_sample.ltx")
    ini_trade.read_raw(inspect.cleandoc("""
        [trade_buy]
        /^af_/              = 0.1, 0.1
        /^ammo_/            = 0.2, 0.2
        /^grenade_/         = 0.3, 0.3
        /^wpn_addon_/       = 0.4, 0.4
        /^wpn_/             = 0.5, 0.5
        /_outfit$/          = 0.4, 0.8
        /^mutant_/          = 0.3, 1.1

        bandage             = 0.1, 0.1
        medkit              = 0.1, 0.1
        medkit_army         = 0.2, 0.2
        medkit_scientic     = 0.3, 0.3
        antirad             = 0.4, 0.6

        bread               ;NO TRADE
        kolbasa             ;NO TRADE
        conserva            ;NO TRADE
        energy_drink        ;NO TRADE
        vodka               ;NO TRADE
    """))
    return TradeBuyImpl(ini_trade.section("trade_buy"))

def test_sample_direct_unlisted(trade_sample):
    trade: TradeBuyImpl = trade_sample
    assert trade.get_buy_k("detector_simple") == pytest.approx(1.0, abs=1e-6)
    assert trade.get_buy_k("guitar_a") == pytest.approx(1.0, abs=1e-6)
    assert trade.get_buy_k("bolt") == pytest.approx(1.0, abs=1e-6)

def test_sample_direct_without_koefs(trade_sample):
    trade: TradeBuyImpl = trade_sample
    assert trade.get_buy_k("bread") == pytest.approx(0.0, abs=1e-6)
    assert trade.get_buy_k("kolbasa") == pytest.approx(0.0, abs=1e-6)
    assert trade.get_buy_k("conserva") == pytest.approx(0.0, abs=1e-6)
    assert trade.get_buy_k("energy_drink") == pytest.approx(0.0, abs=1e-6)
    assert trade.get_buy_k("vodka") == pytest.approx(0.0, abs=1e-6)

def test_sample_direct_with_koefs(trade_sample):
    trade: TradeBuyImpl = trade_sample
    assert trade.get_buy_k("bandage") == pytest.approx(0.1, abs=1e-6)
    assert trade.get_buy_k("medkit") == pytest.approx(0.1, abs=1e-6)
    assert trade.get_buy_k("medkit_army") == pytest.approx(0.2, abs=1e-6)
    assert trade.get_buy_k("medkit_scientic") == pytest.approx(0.3, abs=1e-6)
    assert trade.get_buy_k("antirad") == pytest.approx(0.5, abs=1e-6)

def test_sample_regex_with_koefs(trade_sample):
    trade: TradeBuyImpl = trade_sample
    assert trade.get_buy_k("af_medusa") == pytest.approx(0.1, abs=1e-6)
    assert trade.get_buy_k("ammo_9x18_fmj") == pytest.approx(0.2, abs=1e-6)
    assert trade.get_buy_k("grenade_f1") == pytest.approx(0.3, abs=1e-6)
    assert trade.get_buy_k("wpn_addon_silencer") == pytest.approx(0.4, abs=1e-6)
    assert trade.get_buy_k("wpn_pm") == pytest.approx(0.5, abs=1e-6)
    assert trade.get_buy_k("novice_outfit") == pytest.approx(0.6, abs=1e-6)
    assert trade.get_buy_k("mutant_flesh_eye") == pytest.approx(0.7, abs=1e-6)

# ----------------------------------------------------------------

def test_meta_trade_buy_koefs():
    trade = TradeBuy()

    # listed
    assert trade.get_buy_k("af_medusa") == pytest.approx(0.65, abs=1e-6)
    assert trade.get_buy_k("ammo_9x18_fmj") == pytest.approx(0.50, abs=1e-6)
    assert trade.get_buy_k("ammo_og-7b") == pytest.approx(0.50, abs=1e-6)
    assert trade.get_buy_k("ammo_vog-25") == pytest.approx(0.50, abs=1e-6)
    assert trade.get_buy_k("grenade_f1") == pytest.approx(0.50, abs=1e-6)
    assert trade.get_buy_k("wpn_fn2000") == pytest.approx(0.20, abs=1e-6)
    assert trade.get_buy_k("wpn_addon_scope") == pytest.approx(0.45, abs=1e-6)
    assert trade.get_buy_k("protection_outfit") == pytest.approx(0.65, abs=1e-6)
    assert trade.get_buy_k("medkit") == pytest.approx(0.75, abs=1e-6)
    assert trade.get_buy_k("mutant_snork_leg") == pytest.approx(0.00, abs=1e-6)
    assert trade.get_buy_k("bread") == pytest.approx(0.20, abs=1e-6)
    assert trade.get_buy_k("device_torch") == pytest.approx(0.00, abs=1e-6)
    assert trade.get_buy_k("detector_simple") == pytest.approx(0.00, abs=1e-6)
    assert trade.get_buy_k("device_pda") == pytest.approx(0.75, abs=1e-6)
    assert trade.get_buy_k("hand_radio") == pytest.approx(0.00, abs=1e-6)
    assert trade.get_buy_k("guitar_a") == pytest.approx(0.20, abs=1e-6)
    assert trade.get_buy_k("quest_case_01") == pytest.approx(0.00, abs=1e-6)
    assert trade.get_buy_k("outfit_exo_m1") == pytest.approx(0.65, abs=1e-6)
    assert trade.get_buy_k("wpn_rg6_m1") == pytest.approx(0.65, abs=1e-6)
    assert trade.get_buy_k("wpn_pm_arena") == pytest.approx(0.00, abs=1e-6)

    # unlisted
    assert trade.get_buy_k("crazy_flash") == pytest.approx(1.00, abs=1e-6)

def test_meta_singleton():
    trade_1 = TradeBuy()
    trade_2 = TradeBuy()
    assert trade_1 is trade_2

# ----------------------------------------------------------------
