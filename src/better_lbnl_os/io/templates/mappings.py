"""Header/fuel/unit mappings for template readers (kept intentionally small)."""

# BETTER Excel (EN/FR/ES) headers for metadata and utility bills
BETTER_META_HEADERS = {
    # canonical -> variants
    "BLDG_ID": [
        "Building ID*", "Building ID",
        "ID du bâtiment*", "ID du bâtiment",
        "Edificio ID*", "Edificio ID",
    ],
    "BLDG_NAME": [
        "Building Name*", "Building Name",
        "Nom du bâtiment*", "Nom du bâtiment",
        "Nombre del edificio*", "Nombre del edificio",
    ],
    "LOCATION": [
        "Location*", "Location",
        "Emplacement*", "Emplacement",
        "Ubicación*", "Ubicación",
    ],
    "FLOOR_AREA": [
        "Gross Floor Area (Excluding Parking)*", "Gross Floor Area (Excluding Parking)",
        "Surface brute de plancher (hors parking)*", "Surface brute de plancher (hors parking)",
        "Superficie total (sin estacionamiento)*", "Superficie total (sin estacionamiento)",
    ],
    "SPACE_TYPE": [
        "Primary Building Space Type*", "Primary Building Space Type",
        "Type d'espace primaire du bâtiment*", "Type d'espace primaire du bâtiment",
        "Tipo de uso principal*", "Tipo de uso principal",
    ],
}

BETTER_BILLS_HEADERS = {
    "BLDG_ID": [
        "Building ID*", "Building ID",
        "Edificio ID*", "Edificio ID",
        "ID du bâtiment*", "ID du bâtiment",
    ],
    "START": [
        "Billing Start Dates*", "Billing Start Date*", "Billing Start Dates", "Billing Start Date",
        "Dates de début de facturation*", "Dates de début de facturation",
        "Fechas de inicio de facturación*", "Fechas de inicio de facturación",
    ],
    "END": [
        "Billing End Dates*", "Billing End Date*", "Billing End Dates", "Billing End Date",
        "Dates de fin de facturation*", "Dates de fin de facturation",
        "Fechas de finalización de facturación*", "Fechas de finalización de facturación",
    ],
    "FUEL": [
        "Energy Type*", "Energy Type",
        "Tipo de energía*", "Tipo de energía",
        "Type d'énergie*", "Type d'énergie",
    ],
    "UNIT": [
        "Energy Unit*", "Energy Unit",
        "Unidad de energía*", "Unidad de energía",
        "Unité d'énergie*", "Unité d'énergie",
    ],
    "CONSUMPTION": [
        "Energy Consumption*", "Energy Consumption",
        "Consumo de energía*", "Consumo de energía",
        "Consommation d'énergie*", "Consommation d'énergie",
    ],
    "COST": [
        "Energy Cost", "Energy Cost ($)",
        "Coût de l'énergie",
        "Costo de energía",
    ],
}

# PM headers (canonical, case-sensitive as exported)
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

# Simple fuel mapping (expand as needed)
FUEL_NAME_MAP = {
    # BETTER canonical English labels already provided by template; keep a few PM variants
    "Electric": "ELECTRICITY",
    "Electricity": "ELECTRICITY",
    "Natural Gas": "NATURAL_GAS",
    "Gas": "NATURAL_GAS",
}

# Simple unit mapping (expand as needed)
UNIT_NAME_MAP = {
    "kWh": "kWh",
    "MWh": "MWh",
    "therms": "therms",
    "Therms": "therms",
}

