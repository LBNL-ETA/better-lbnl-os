"""Constants for template parsing."""

# Area conversion
SQFT_TO_SQM = 0.092903

# Template column headers for BETTER Excel (EN/FR/ES)
BETTER_META_HEADERS = {
    # canonical -> variants
    "BLDG_ID": [
        "Building ID*",
        "ID du bâtiment*",
        "Edificio ID*",
    ],
    "BLDG_NAME": [
        "Building Name*",
        "Nom du bâtiment*",
        "Nombre del edificio*",
    ],
    "LOCATION": [
        "Location*",
        "Emplacement*",
        "Ubicación*",
    ],
    "FLOOR_AREA": [
        "Gross Floor Area (Excluding Parking)*",
        "Surface brute de plancher (hors parking)*",
        "Superficie total (sin estacionamiento)*",
    ],
    "SPACE_TYPE": [
        "Primary Building Space Type*",
        "Type d'espace primaire du bâtiment*",
        "Tipo de uso principal*",
    ],
}

BETTER_BILLS_HEADERS = {
    "BLDG_ID": [
        "Building ID*",
        "Edificio ID*",
        "ID du bâtiment*",
    ],
    "START": [
        "Billing Start Dates*",
        "Billing Start Date*",
        "Dates de début de facturation*",
        "Fechas de inicio de facturación*",
    ],
    "END": [
        "Billing End Dates*",
        "Billing End Date*",
        "Dates de fin de facturation*",
        "Fechas de finalización de facturación*",
    ],
    "FUEL": [
        "Energy Type*",
        "Tipo de energía*",
        "Type d'énergie*",
    ],
    "UNIT": [
        "Energy Unit*",
        "Unidad de energía*",
        "Unité d'énergie*",
    ],
    "CONSUMPTION": [
        "Energy Consumption*",
        "Consumo de energía*",
        "Consommation d'énergie*",
    ],
    "COST": [
        "Energy Cost",
        "Coût de l'énergie",
        "Costo de energía",
    ],
}

# Portfolio Manager headers
PM_META_HEADERS = {
    "PM_ID": "Portfolio Manager ID",
    "PROP_NAME": "Property Name",
    "CITY": "City/Municipality",
    "STATE": "State/Province",
    "POSTAL": "Postal Code",
    "GFA_UNITS": "GFA Units",
    "GFA": "Gross Floor Area",
    "SPACE_TYPE": "Property Type - Self-Selected",
}

PM_BILLS_HEADERS = {
    "PM_ID": "Portfolio Manager ID",
    "START": "Start Date",
    "END": "End Date",
    "DELIVERY": "Delivery Date",
    "METER_TYPE": "Meter Type",
    "USAGE_UNITS": "Usage Units",
    "USAGE_QTY": "Usage/Quantity",
    "COST": "Cost ($)",
}

# Fuel type mappings (expand as needed)
FUEL_NAME_MAP = {
    # Common variations
    "Electric": "ELECTRICITY",
    "Electricity": "ELECTRICITY",
    "Natural Gas": "NATURAL_GAS",
    "Gas": "NATURAL_GAS",
    "Fuel Oil": "FUEL_OIL",
    "Fuel Oil #2": "FUEL_OIL",
    "District Steam": "DISTRICT_STEAM",
    "District Hot Water": "DISTRICT_HOT_WATER",
    "District Chilled Water": "DISTRICT_CHILLED_WATER",
}

# Unit mappings (expand as needed)
UNIT_NAME_MAP = {
    # Electricity
    "kWh": "kWh",
    "MWh": "MWh",
    "kWh (thousand Watt-hours)": "kWh",
    # Natural gas
    "therms": "therms",
    "Therms": "therms",
    "CCF": "CCF",
    "MCF": "MCF",
    "ccf": "CCF",
    # Oil
    "gallons": "gallons",
    "Gallons": "gallons",
}
