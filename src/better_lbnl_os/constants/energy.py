"""Energy conversion factors and related constants."""

CONVERSION_TO_KWH: dict[tuple[str, str], float] = {
    ("ELECTRICITY", "kWh"): 1.0,
    ("ELECTRICITY", "MWh"): 1000.0,
    ("NATURAL_GAS", "therms"): 29.3,
    ("NATURAL_GAS", "ccf"): 29.3,
    ("NATURAL_GAS", "mcf"): 293.0,
    ("NATURAL_GAS", "MMBtu"): 293.0,
    ("FUEL_OIL", "gallons"): 40.6,
    ("PROPANE", "gallons"): 27.0,
    ("STEAM", "MLbs"): 293.0,
    ("STEAM", "therms"): 29.3,
}

