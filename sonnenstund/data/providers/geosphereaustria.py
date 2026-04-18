from typing import Self

import requests
import pandas as pd
import geopandas as gpd
from sonnenstund.data import LocationData
from sonnenstund.data.dataprovider import DataProvider

from datetime import date
from shapely.geometry import Point

from sonnenstund.models.geosphereaustria.model import (
    StationHistoricalMetadataModel,
    StationMetadata,
)
from functools import cached_property


class _GeosphereAustriaLocationData(LocationData):
    def __init__(self, data: pd.DataFrame | None = None):
        self.data = data
        super().__init__()

    @property
    def _geopandas_df(self) -> gpd.GeoDataFrame:
        # TODO implement
        return gpd.GeoDataFrame(self.data)

    @classmethod
    def from_api_response(cls, response: dict) -> Self:
        # TODO implement
        return cls(None)


class _GeosphereAustria(DataProvider):
    base_url: str = "https://dataset.api.hub.geosphere.at/v1"

    @cached_property
    def _stations(self) -> list[StationMetadata]:
        response = requests.get(
            f"{self.base_url}/station/historical/klima-v2-1d/metadata"
        ).json()
        metadata_model = StationHistoricalMetadataModel(**response)
        return metadata_model.stations

    @classmethod
    def get_historical_location_data(
        cls,
        time_from: date,
        time_to: date,
        location: list[Point],
        radius: float | None = None,
    ) -> LocationData:
        return _GeosphereAustriaLocationData()
