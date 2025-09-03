"""Energy conversion factors and related constants."""

CONVERSION_TO_KWH: dict[tuple[str, str], float] = {
    # Electricity variations
    ("ELECTRICITY", "kWh"): 1.0,
    ("ELECTRICITY", "MWh"): 1000.0,
    ("Electric - Grid", "kWh"): 1.0,
    ("Electric - Grid", "MWh"): 1000.0,
    # Natural Gas
    ("NATURAL_GAS", "therms"): 29.3,
    ("NATURAL_GAS", "Therms"): 29.3,
    ("NATURAL_GAS", "ccf"): 29.3,
    ("NATURAL_GAS", "CCF"): 29.3,
    ("NATURAL_GAS", "mcf"): 293.0,
    ("NATURAL_GAS", "MCF"): 293.0,
    ("NATURAL_GAS", "MMBtu"): 293.0,
    # Fuel Oil
    ("FUEL_OIL", "gallons"): 40.6,
    ("FUEL_OIL", "Gallons"): 40.6,
    # Other fuels
    ("PROPANE", "gallons"): 27.0,
    ("PROPANE", "Gallons"): 27.0,
    ("STEAM", "MLbs"): 293.0,
    ("STEAM", "therms"): 29.3,
    ("STEAM", "Therms"): 29.3,
}

