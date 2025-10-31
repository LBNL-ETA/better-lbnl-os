import pytest

from better_lbnl_os.core import defaults


def test_normalize_state_code_handles_abbreviation_and_full_name():
    assert defaults.normalize_state_code("ca") == "CA"
    assert defaults.normalize_state_code("California") == "CA"
    assert defaults.normalize_state_code("   ") is None
    assert defaults.normalize_state_code("unknown") is None
    assert defaults.normalize_state_code(None) is None


def test_infer_state_from_address_variations():
    assert defaults.infer_state_from_address("123 Main St, Berkeley, CA") == "CA"
    assert defaults.infer_state_from_address("Berkeley CA 94704") == "CA"
    assert defaults.infer_state_from_address("A longer location description") is None


def test_get_default_fuel_price_prefers_state_value():
    price = defaults.get_default_fuel_price("ELECTRICITY", "CA", "US")
    assert price == pytest.approx(0.2233, rel=1e-4)

    assert defaults.get_default_fuel_price("UNKNOWN", "CA", "US") is None
    assert defaults.get_default_fuel_price("ELECTRICITY", "ZZ", "US") is None


def test_get_default_fuel_price_uses_international_fallback():
    price = defaults.get_default_fuel_price("ELECTRICITY", None, "CA")
    assert price == pytest.approx(0.11014902, rel=1e-4)


def test_lookup_egrid_subregion_normalizes_zipcode():
    assert defaults.lookup_egrid_subregion("00012") == "CAMX"
    assert defaults.lookup_egrid_subregion("invalid") is None


def test_get_electric_emission_factor_prefers_region_then_default():
    region_factors = defaults.get_electric_emission_factor("AKMS", None)
    assert region_factors is not None
    assert region_factors["CO2"] == pytest.approx(0.238176, rel=1e-3)

    country_factors = defaults.get_electric_emission_factor(None, "ca")
    assert country_factors is not None
    assert country_factors["CO2"] == pytest.approx(0.109434, rel=1e-3)

    default_factors = defaults.get_electric_emission_factor(None, "FR")
    assert default_factors is not None
    assert "CO2" in default_factors


def test_get_fossil_emission_factor_returns_expected_group():
    factors = defaults.get_fossil_emission_factor("NATURAL_GAS")
    assert factors is not None
    assert factors["CO2"] == pytest.approx(0.18108, rel=1e-5)


def test_get_fossil_emission_factor_returns_none_when_group_missing(monkeypatch):
    original_loader = defaults._load_fossil_factors
    original_loader.cache_clear()
    monkeypatch.setattr(defaults, "_load_fossil_factors", lambda: {})
    assert defaults.get_fossil_emission_factor("NATURAL_GAS") is None
    monkeypatch.setattr(defaults, "_load_fossil_factors", original_loader)
    original_loader.cache_clear()
