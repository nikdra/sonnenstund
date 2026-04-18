from abc import ABC, abstractmethod

from sonnenstund.data import LocationData
from datetime import date
from shapely.geometry import Point


class DataProvider(ABC):
    @classmethod
    @abstractmethod
    def get_historical_location_data(
        cls,
        time_from: date,
        time_to: date,
        location: list[Point],
        radius: float | None = None,
    ) -> LocationData:
        """Retrieve all data from a specified location and radius (in km).
        If the radius is None, data from the clostest location to the specified location will be retrieved.
        If there is more than one location specified, the radius will be ignored and only data from the specified locations will be retrieved.

        Args:
            time_from (date): Start of the time range for which data should be retrieved.
            time_to (date): End of the time range for which data should be retrieved.
            location ([Point]): List of locations for which data should be retrieved.
            radius (float | None, optional): Radius in kilometers a location for which data should be retrieved. Defaults to None.

        Returns:
            LocationData: LocationData object containing the retrieved data.
        """
        pass
