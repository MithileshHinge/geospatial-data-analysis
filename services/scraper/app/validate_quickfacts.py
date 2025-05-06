from models.geo_info import GeoInfo


def clean_quickfacts_csv(csv_content: list[list[str]]):
    """
    Remove every Notes column (Fact Note and Value Note for <geography name>).
    Remove all rows after "FIPS Code" (Footnotes are included at the end of the file).
    Remove quotes from FIPS Codes values.
    """

    headers = csv_content[0]
    notes_indices = [
        i
        for i, header in enumerate(headers)
        if header == "Fact Note" or header.startswith("Value Note for")
    ]
    cleaned_csv_content: list[list[str]] = []
    for row in csv_content:
        row = [row[i] for i in range(0, len(row)) if i not in notes_indices]
        cleaned_csv_content.append(row)
        if row[0] == "FIPS Code":
            break

    # Remove quotes from FIPS Codes values
    cleaned_csv_content[-1] = [
        value.replace('"', "") for value in cleaned_csv_content[-1]
    ]

    return cleaned_csv_content


def validate_quickfacts_csv(
    cleaned_csv_content: list[list[str]],
    geo_info_batch: list[GeoInfo],
):
    """
    Validate the QuickFacts CSV file.

    Args:
        cleaned_csv_content (list[list[str]]): The cleaned QuickFacts CSV content (use clean_quickfacts_csv to clean it)
        geo_info_batch (list[GeoInfo]): The batch of GeoInfo objects used to generate the QuickFacts CSV file

    Returns:
        list[GeoInfo]: GeoInfo objects for the geographies that are missing from the QuickFacts CSV file
    """
    assert len(geo_info_batch) <= 6, (
        "QuickFacts CSV files can only contain 6 geographies at max"
    )

    labels = cleaned_csv_content[0][1:]
    fips_codes = cleaned_csv_content[-1][1:]

    missing_geo_infos: list[GeoInfo] = []
    missing_fips_codes: list[str] = []

    for geo_info in geo_info_batch:
        if geo_info.label not in labels:
            missing_geo_infos.append(geo_info)
        if geo_info.geoid not in fips_codes:
            missing_fips_codes.append(geo_info.geoid)

    return missing_geo_infos, missing_fips_codes
