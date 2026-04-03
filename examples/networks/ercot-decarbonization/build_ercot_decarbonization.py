# SPDX-FileCopyrightText: PyPSA Contributors
#
# SPDX-License-Identifier: MIT

"""
Build an ERCOT decarbonization example network and export it.

This script programmatically creates a simplified 4-zone representation of the
ERCOT (Texas) grid with existing thermal generation, extendable renewables,
battery storage, hydrogen long-duration storage, inter-zonal transmission,
and a CO2 emissions cap to study decarbonization pathways.
"""

from pathlib import Path

import numpy as np
import pandas as pd

import pypsa


def build_network() -> pypsa.Network:
    """Build and return the ERCOT decarbonization network."""
    rng = np.random.default_rng(42)

    # ---- Network and snapshots ----
    n = pypsa.Network(name="ERCOT-Decarbonization")
    snapshots = pd.date_range("2035-01-01", periods=2920, freq="3h")
    n.set_snapshots(snapshots)

    hour_of_day = snapshots.hour
    day_of_year = snapshots.dayofyear

    # ---- Carriers ----
    n.add("Carrier", "onshore_wind", co2_emissions=0.0)
    n.add("Carrier", "solar", co2_emissions=0.0)
    n.add("Carrier", "natural_gas", co2_emissions=0.19)
    n.add("Carrier", "coal", co2_emissions=0.34)
    n.add("Carrier", "nuclear", co2_emissions=0.0)
    n.add("Carrier", "battery", co2_emissions=0.0)
    n.add("Carrier", "hydrogen", co2_emissions=0.0)
    n.add("Carrier", "AC", co2_emissions=0.0)

    # ---- Buses ----
    for zone in ["Houston", "North", "South", "West"]:
        n.add("Bus", zone, carrier="AC")
    n.add("Bus", "Houston H2", carrier="hydrogen")

    # ---- Loads ----
    base_loads = {"Houston": 15000, "North": 12000, "South": 8000, "West": 5000}
    for zone, base in base_loads.items():
        # Seasonal: peak in summer (day ~180)
        seasonal = 1 + 0.15 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        # Diurnal: peak in afternoon
        diurnal = 1 + 0.10 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
        noise = 1 + 0.02 * rng.standard_normal(len(snapshots))
        load_profile = base * seasonal * diurnal * noise
        n.add("Load", f"{zone} load", bus=zone, p_set=load_profile)

    # ---- Existing (non-extendable) generators ----
    n.add(
        "Generator",
        "Houston gas CCGT",
        bus="Houston",
        carrier="natural_gas",
        p_nom=8000,
        efficiency=0.55,
        marginal_cost=35,
    )
    n.add(
        "Generator",
        "Houston coal",
        bus="Houston",
        carrier="coal",
        p_nom=3000,
        efficiency=0.38,
        marginal_cost=25,
    )
    n.add(
        "Generator",
        "North gas CCGT",
        bus="North",
        carrier="natural_gas",
        p_nom=6000,
        efficiency=0.55,
        marginal_cost=35,
    )
    n.add(
        "Generator",
        "North nuclear",
        bus="North",
        carrier="nuclear",
        p_nom=2400,
        marginal_cost=9,
        efficiency=0.33,
    )
    n.add(
        "Generator",
        "South gas CT",
        bus="South",
        carrier="natural_gas",
        p_nom=4000,
        efficiency=0.35,
        marginal_cost=55,
    )
    n.add(
        "Generator",
        "West gas CT",
        bus="West",
        carrier="natural_gas",
        p_nom=2000,
        efficiency=0.35,
        marginal_cost=55,
    )

    # ---- Extendable renewable generators with synthetic CF ----
    # Wind capacity factor: seasonal + diurnal pattern + noise
    def wind_cf(mean: float = 0.35) -> np.ndarray:
        seasonal = 0.05 * np.cos(2 * np.pi * (day_of_year - 30) / 365)
        diurnal = 0.03 * np.sin(2 * np.pi * (hour_of_day - 3) / 24)
        noise = 0.10 * rng.standard_normal(len(snapshots))
        cf = mean + seasonal + diurnal + noise
        return np.clip(cf, 0, 1)

    # Solar capacity factor: zero at night, bell curve during day
    def solar_cf(mean_peak: float = 0.55) -> np.ndarray:
        # Sunrise ~6, sunset ~18 roughly
        solar_angle = np.pi * (hour_of_day - 6) / 12
        daytime = (hour_of_day >= 6) & (hour_of_day <= 18)
        bell = np.where(daytime, np.sin(np.clip(solar_angle, 0, np.pi)), 0.0)
        seasonal = 1 + 0.15 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        noise = 1 + 0.05 * rng.standard_normal(len(snapshots))
        cf = mean_peak * bell * seasonal * noise
        return np.clip(cf, 0, 1)

    n.add(
        "Generator",
        "West onshore wind",
        bus="West",
        carrier="onshore_wind",
        p_nom_extendable=True,
        capital_cost=110000,
        p_nom_max=30000,
        p_max_pu=wind_cf(mean=0.35),
    )
    n.add(
        "Generator",
        "Houston solar",
        bus="Houston",
        carrier="solar",
        p_nom_extendable=True,
        capital_cost=75000,
        p_nom_max=50000,
        p_max_pu=solar_cf(mean_peak=0.55),
    )
    n.add(
        "Generator",
        "South solar",
        bus="South",
        carrier="solar",
        p_nom_extendable=True,
        capital_cost=75000,
        p_nom_max=40000,
        p_max_pu=solar_cf(mean_peak=0.55),
    )
    n.add(
        "Generator",
        "North onshore wind",
        bus="North",
        carrier="onshore_wind",
        p_nom_extendable=True,
        capital_cost=115000,
        p_nom_max=20000,
        p_max_pu=wind_cf(mean=0.35),
    )

    # ---- Battery storage (one per AC zone) ----
    for zone in ["Houston", "North", "South", "West"]:
        n.add(
            "StorageUnit",
            f"{zone} battery",
            bus=zone,
            carrier="battery",
            p_nom_extendable=True,
            capital_cost=150000,
            max_hours=4,
            efficiency_store=0.95,
            efficiency_dispatch=0.95,
            cyclic_state_of_charge=True,
        )

    # ---- Long-duration H2 storage (Store + Links) ----
    n.add(
        "Store",
        "Houston H2 store",
        bus="Houston H2",
        e_nom_extendable=True,
        capital_cost=10000,
        standing_loss=0.0001,
    )
    n.add(
        "Link",
        "Houston electrolyzer",
        bus0="Houston",
        bus1="Houston H2",
        p_nom_extendable=True,
        efficiency=0.7,
        capital_cost=80000,
        carrier="hydrogen",
    )
    n.add(
        "Link",
        "Houston fuel cell",
        bus0="Houston H2",
        bus1="Houston",
        p_nom_extendable=True,
        efficiency=0.5,
        capital_cost=60000,
        carrier="hydrogen",
    )

    # ---- Inter-zonal transmission links ----
    n.add(
        "Link",
        "Houston-North",
        bus0="Houston",
        bus1="North",
        p_nom=5000,
        p_min_pu=-1,
        p_nom_extendable=True,
        p_nom_min=5000,
        capital_cost=40000,
        carrier="AC",
    )
    n.add(
        "Link",
        "Houston-South",
        bus0="Houston",
        bus1="South",
        p_nom=3000,
        p_min_pu=-1,
        p_nom_extendable=True,
        p_nom_min=3000,
        capital_cost=40000,
        carrier="AC",
    )
    n.add(
        "Link",
        "North-West",
        bus0="North",
        bus1="West",
        p_nom=4000,
        p_min_pu=-1,
        p_nom_extendable=True,
        p_nom_min=4000,
        capital_cost=45000,
        carrier="AC",
    )
    n.add(
        "Link",
        "South-West",
        bus0="South",
        bus1="West",
        p_nom=2000,
        p_min_pu=-1,
        p_nom_extendable=True,
        p_nom_min=2000,
        capital_cost=45000,
        carrier="AC",
    )

    # ---- Global CO2 constraint ----
    n.add(
        "GlobalConstraint",
        "co2_limit",
        type="primary_energy",
        carrier_attribute="co2_emissions",
        sense="<=",
        constant=50e6,
    )

    return n


if __name__ == "__main__":
    n = build_network()

    # Create output directory
    Path("examples/networks/ercot-decarbonization/ercot-decarbonization").mkdir(
        parents=True, exist_ok=True
    )

    # Export in both formats
    n.export_to_csv_folder(
        "examples/networks/ercot-decarbonization/ercot-decarbonization"
    )
    n.export_to_netcdf(
        "examples/networks/ercot-decarbonization/ercot-decarbonization.nc"
    )

    print(n)
