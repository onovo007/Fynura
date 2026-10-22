"""Parser for reviewed UN DESA International Migrant Stock extracts."""

import csv
from datetime import date
from io import StringIO

from backend.models.contextual import ContextObservation

PILOT_ISO3 = {"COD", "KEN", "NGA", "UGA"}
SOURCE_URL = "https://www.un.org/development/desa/pd/content/International-migrant-stock"


class UNDESAMigrantStockAdapter:
    source_id = "undesa_migrant_stock_2024"
    licence_id = "undesa-ims-2024-review-required"

    def parse_reviewed_csv(self, text: str) -> list[ContextObservation]:
        required = {"iso3", "country", "year", "migrant_stock", "source_table"}
        reader = csv.DictReader(StringIO(text))
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("UN DESA reviewed extract has an invalid schema")
        output = []
        for row in reader:
            iso3 = row["iso3"].upper()
            if iso3 not in PILOT_ISO3:
                continue
            year = int(row["year"])
            output.append(ContextObservation(
                source_id=self.source_id, context_type="migrant_stock", geography_name=row["country"],
                geography_code=iso3, geography_level="country", reference_end=date(year, 12, 31),
                value=float(row["migrant_stock"]), unit="persons", source_url=SOURCE_URL,
                method=f"Reviewed extract from {row['source_table']}", licence_id=self.licence_id,
                attribution="United Nations, Department of Economic and Social Affairs, Population Division (2024), International Migrant Stock 2024",
                privacy_classification="public_aggregate", validation_status="quarantined",
                limitations=["Migrant stock is a structural estimate, not a current movement flow.", "Country estimates may be extrapolated where recent empirical sources are unavailable."],
            ))
        return output

