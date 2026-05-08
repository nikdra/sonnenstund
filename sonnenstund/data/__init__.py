from abc import ABC, abstractmethod
from geopandas import GeoDataFrame
from datetime import date
from shapely.geometry import Point
from enum import StrEnum, auto
import pandas as pd


class Parameter(StrEnum):
    """Accepted parameters for Data Providers.
    These are weather data that can be queried:
    SUN_HOURS: number of hours the sun has shined

    Args:
        StrEnum (_type_): _description_
    """

    SUN_HOURS = auto()


class LocationData(ABC):
    @property
    @abstractmethod
    def df(self) -> pd.DataFrame:
        raise NotImplementedError("This method must be implemented by subclasses.")

    @property
    @abstractmethod
    def geopandas_df(self) -> GeoDataFrame:
        raise NotImplementedError("This method must be implemented by subclasses.")


class DataProvider(ABC):
    @staticmethod
    @abstractmethod
    def get_historical_location_data(
        time_from: date,
        time_to: date,
        locations: Point | list[Point],
        parameters: list[Parameter],
        radius: float | None = None,
        quality: bool = False,
    ) -> LocationData | None:
        """Retrieve all data from a specified location and radius (in km).
        If the radius is None, data from the clostest location to the specified location will be retrieved.
        If there is more than one location specified, the radius will be ignored and only data from the specified locations will be retrieved.

        Args:
            time_from (date): Start of the time range for which data should be retrieved.
            time_to (date): End of the time range for which data should be retrieved.
            locations (Point | list[Point]): List of locations for which data should be retrieved.
            radius (float | None, optional): Radius in kilometers a location for which data should be retrieved. Defaults to None.
            parameters (list[Parameter]): List of parameters for which data should be retrieved.
            quality (bool, optional): Whether to include quality information for the retrieved data. Defaults to False.

        Returns:
            LocationData | None: LocationData object containing the retrieved data, or None if no data is available.
        """
        raise NotImplementedError("This method must be implemented by subclasses.")
