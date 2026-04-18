from abc import ABC, abstractmethod
from geopandas import GeoDataFrame


class LocationData(ABC):
    @property
    def df(self) -> GeoDataFrame:
        return self._geopandas_df[
            ["date", "sun_hours", "sun_hours_quality", "geometry"]
        ]

    @property
    @abstractmethod
    def _geopandas_df(self) -> GeoDataFrame:
        pass
