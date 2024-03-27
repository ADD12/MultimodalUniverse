from astropy.coordinates import SkyCoord
from datasets import DatasetBuilder, Dataset
from .utils import get_catalog
import numpy as np
from astropy import units
import pandas as pd


def extract_cat_params(cat: DatasetBuilder):
    cat = get_catalog(cat)
    subcat = pd.DataFrame(
        data=[cat[col] for col in ["ra", "dec", "healpix"]], columns=["ra", "dec", "healpix"]
    )
    return subcat


def build_catalogue(cats: list[DatasetBuilder], names: list[str], matching_radius: float = 1.0):

    # Set the columns for the master catalogue
    master_cat = pd.DataFrame(
        columns=["ra", "dec", "healpix"] + names + [f"{name}_idx" for name in names]
    )

    for cat, name in zip(cats, names):
        # Extract the relevant columns
        cat = extract_cat_params(cat)

        # Match the catalogues
        master_coords = SkyCoord(master_cat.loc[:, "ra"], master_cat.loc[:, "dec"], unit="deg")
        cat_coords = SkyCoord(cat.loc[:, "ra"], cat.loc[:, "dec"], unit="deg")
        idx, sep2d, _ = master_coords.match_to_catalog_sky(cat_coords)
        mask = sep2d < matching_radius * units.arcsec

        # Update the matching columns
        master_cat[name][idx[mask]] = True
        master_cat[name + "_idx"][idx[mask]] = idx[mask]

        # Add new rows to the master catalogue
        name_data = []
        name_idx_data = []
        for subname in names:
            if subname != name:
                name_data.append(np.zeros(np.sum(~mask), dtype=bool))
                name_idx_data.append(np.nan * np.oness(np.sum(~mask), dtype=int))
            else:
                name_data.append(np.ones(np.sum(~mask), dtype=bool))
                name_idx_data.append(idx[~mask])
        append_cat = pd.DataFrame(
            columns=["ra", "dec", "healpix"] + names + [f"{name}_idx" for name in names]
            data=[cat.loc[~mask, col] for col in ["ra", "dec", "healpix"]] + name_data + name_idx_data 
        )

        master_cat = pd.concat([master_cat, append_cat], ignore_index=True)

    return master_cat