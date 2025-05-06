import logging
from pathlib import Path
from typing import Dict
import pandas as pd

from tsg_common.db.models import QuickFacts

LAYERS = {
    2: "states",
    5: "counties",
    7: "places",
}


def _layer_from_geoid(geoid: str) -> str | None:
    return LAYERS.get(len(geoid))


def parse_quickfacts(
    path: Path,
) -> tuple[Dict[str, str], list[QuickFacts], Dict[str, set[str]]]:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)

    # last row is FIPS codes; identify region columns dynamically
    fips_row: pd.Series[str] = df.iloc[-1, 1:]

    name_map: Dict[str, str] = {}
    facts_rows: list[QuickFacts] = []
    geo_sets: Dict[str, set[str]] = {layer: set() for layer in LAYERS.values()}

    for col_name, geoid in fips_row.items():
        if not geoid or not geoid.isdigit():
            logging.info(f"Invalid FIPS code: {geoid}")
            continue

        layer = _layer_from_geoid(geoid)
        if layer is None:
            logging.info(f"Invalid FIPS code: {geoid}")
            continue

        name_map[geoid] = str(col_name)
        geo_sets[layer].add(geoid)

        facts_json = df.loc[:, ["Fact", col_name]].set_index("Fact")[col_name].to_dict()

        facts_rows.append(
            QuickFacts(
                layer=layer,
                geoid=geoid,
                facts=facts_json,
            )
        )

    return name_map, facts_rows, geo_sets
