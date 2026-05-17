"""GeoSphere Austria provider implementation for historical weather data."""

from typing import Any, Self

import requests
import pandas as pd
import geopandas as gpd
from sonnenstund.data import LocationData, DataProvider, Parameter

from datetime import date
from shapely.geometry import Point

from sonnenstund.models.geosphereaustria.model import (
    GeoJSONFeatureParameter,
    StationHistoricalMetadataModel,
    StationMetadata,
    StationGeoJSONSerializer,
)
from functools import cache

from geopy.distance import geodesic, Distance

import logging

from sonnenstund.models.quality import Quality

logger = logging.getLogger(__name__)

BASE_URL: str = "https://dataset.api.hub.geosphere.at/v1"

# For all points, we store them in longitude, latitude format (EPSG:4326), which is the format used by GeoPandas

PARAMETER_MAPPING: dict[Parameter, str] = {
    Parameter.SUN_HOURS: "so_h",
}

QUALITY_PARAMETER: dict[Parameter, str] = {Parameter.SUN_HOURS: "so_h_flag"}

REVERSE_PARAMETER_MAPPING: dict[str, Parameter] = {
    v: k for k, v in PARAMETER_MAPPING.items()
}
REVERSE_QUALITY_PARAMETER_MAPPING: dict[str, str] = {
    v: f"{k}_quality" for k, v in QUALITY_PARAMETER.items()
}


def _map_quality_flag(flag: float | None) -> Quality:
    """Map an API quality flag to an internal Quality value.

    Args:
        flag (float | None): Raw quality flag from the API.

    Returns:
        Quality: Internal quality classification.
    """
    if flag is None:
        return Quality.UNKNOWN
    if flag < 10:
        return Quality.LOW
    if flag < 20:
        return Quality.MEDIUM
    return Quality.HIGH


PARAMETER_FUNCTIONS = {
    "so_h": lambda x: (
        x
    ),  # sun hours are already in the correct format, so we can just return them as they are
    "so_h_flag": _map_quality_flag,  # we need to map the quality flag to our internal quality representation
}


@cache
def _station_historical_metadata() -> StationHistoricalMetadataModel:
    """Fetch station historical metadata from the GeoSphere Austria API.

    Returns:
        StationHistoricalMetadataModel: Parsed station metadata response.

    Raises:
        Exception: Propagates any exception raised during the API request.
    """
    logger.info("Fetching station historical metadata from GeoSphere Austria API")
    try:
        response = requests.get(
            f"{BASE_URL}/station/historical/klima-v2-1d/metadata"
        ).json()
        return StationHistoricalMetadataModel(**response)
    except Exception as e:
        logger.error(
            f"Error fetching station historical metadata from GeoSphere Austria API: {e}"
        )
        raise e


@cache
def _stations() -> list[StationMetadata]:
    """Return active station metadata from cached API metadata.

    Returns:
        list[StationMetadata]: Active stations from GeoSphere Austria.
    """
    logger.info("Fetching station metadata from GeoSphere Austria API")
    return [s for s in _station_historical_metadata().stations if s.is_active]


@cache
def _stations_locations() -> list[Point]:
    """Return point geometries for each active station.

    Returns:
        list[Point]: Station locations in longitude/latitude order.
    """
    # GeoSphere Austria stores locations in latitude and longitude (EPSG:4326)
    # GeoPandas stores locations in longitute, latitude format
    logger.info("Extracting station locations from station metadata")
    return [Point(station.lon, station.lat) for station in _stations()]


def _distance(point1: Point, point2: Point) -> Distance:
    """Return the geodesic distance between two points.

    Args:
        point1 (Point): First location in longitude/latitude order.
        point2 (Point): Second location in longitude/latitude order.

    Returns:
        Distance: Geodesic distance between the two points.
    """
    logger.info(
        f"Calculating geodesic distance between two points: {point1} and {point2}"
    )
    # Points must be in (latitude, longitude) format for geodesic distance calculation, but GeoPandas stores locations in longitute, latitude format
    return geodesic((point1.y, point1.x), (point2.y, point2.x))


def _nearest_points(point: Point, points: list[Point]) -> Point | None:
    """Find the closest point from a list of candidate points.

    Args:
        point (Point): Reference location.
        points (list[Point]): Candidate locations.

    Returns:
        Point | None: The nearest point, or None if no candidates are provided.
    """
    if len(points) == 0:
        logger.info("No points provided to find nearest point, returning None")
        return None
    logger.info(f"Finding nearest points to a given location: {point}")
    closest_point = None
    closest_distance = None
    for p in points:
        distance = _distance(point, p)
        if closest_distance is None or distance < closest_distance:
            closest_distance = distance
            closest_point = p
    logger.info(
        f"Closest point to {point} is {closest_point} with a distance of {closest_distance}"
    )
    return closest_point


def _get_closest_station(location: Point) -> StationMetadata:
    """Return the metadata for the station closest to the given location.

    Args:
        location (Point): Reference location in longitude/latitude order.

    Returns:
        StationMetadata: Metadata for the closest active station.

    Raises:
        ValueError: If no station can be found for the location.
    """
    logger.info(f"Finding closest station to location: {location}")
    closest_station_location = _nearest_points(location, _stations_locations())
    # pick first station with the same location as the closest station location (there can be multiple stations at the same location, but we only need one of them)
    closest_station = next(
        (
            station
            for station in _stations()
            if Point(station.lon, station.lat) == closest_station_location
        ),
        None,
    )
    if closest_station is not None:
        logger.info(f"Closest station to {location} is {closest_station.name}")
        return closest_station
    logger.error(f"No station found for location {location}")
    raise ValueError(f"No station found for location {location}")


def _get_stations_within_radius(
    location: Point, radius: float
) -> list[StationMetadata]:
    """Returns a list of stations within the specified radius

    Args:
        location (Point): location from which to draw the radius (in EPSG:4326 format, i.e. latitude and longitude)
        radius (float): radius in kilometers

    Returns:
        list[StationMetadata]: list of stations within the specified radius
    """
    logger.info(
        f"Finding stations within a radius of {radius} km from location: {location}"
    )
    return [
        station
        for station, station_location in zip(_stations(), _stations_locations())
        if _distance(location, station_location) <= radius
    ]


class _GeoSphereAustriaHistoricalStationLocationData(LocationData):
    """Historical location data returned by the GeoSphere Austria provider."""

    def __init__(self, data: pd.DataFrame):
        self.data = data
        super().__init__()

    @property
    def geopandas_df(self) -> gpd.GeoDataFrame:
        """Return the data as a GeoPandas GeoDataFrame."""
        return gpd.GeoDataFrame(self.data)

    @property
    def df(self) -> pd.DataFrame:
        """Return the data as a pandas DataFrame."""
        return self.data

    @classmethod
    def _from_api_response(
        cls, response: StationGeoJSONSerializer, api_parameters: set[str]
    ) -> Self:
        """Build a station location data container from API response data.

        Args:
            response (StationGeoJSONSerializer): Parsed API response.
            api_parameters (set[str]): API parameter keys contained in the response.

        Returns:
            _GeoSphereAustriaHistoricalStationLocationData: Data container with mapped values.
        """
        quality_parameters = {
            p for p in api_parameters if p in REVERSE_QUALITY_PARAMETER_MAPPING
        }
        value_parameters = {p for p in api_parameters if p in REVERSE_PARAMETER_MAPPING}

        def _map_data(parameters: dict[str, GeoJSONFeatureParameter]) -> dict[str, Any]:
            data = {}
            for parameter, value in parameters.items():
                if parameter in quality_parameters:
                    data[REVERSE_QUALITY_PARAMETER_MAPPING[parameter]] = [
                        PARAMETER_FUNCTIONS[parameter](v) for v in value.data
                    ]
                if parameter in value_parameters:
                    data[REVERSE_PARAMETER_MAPPING[parameter]] = [
                        PARAMETER_FUNCTIONS[parameter](v) for v in value.data
                    ]
            return data

        dates = [t.date().isoformat() for t in response.timestamps]
        df = pd.DataFrame(
            columns=["date", "geometry"]
            + [REVERSE_PARAMETER_MAPPING[p] for p in value_parameters]
            + [REVERSE_QUALITY_PARAMETER_MAPPING[p] for p in quality_parameters]
        )
        for feature in response.features:
            geometry = Point(
                *feature.geometry.coordinates[::-1]
            )  # read coordinates in reverse order
            data = _map_data(feature.properties.parameters)
            d = {"date": dates, "geometry": geometry, **data}
            df = pd.concat([df, pd.DataFrame(d)], ignore_index=True)
        return cls(df)


def _get_data_for_stations(
    stations: list[StationMetadata],
    time_from: date,
    time_to: date,
    parameters: list[Parameter],
    quality: bool = False,
) -> _GeoSphereAustriaHistoricalStationLocationData:
    """Query the GeoSphere Austria API to retrieve station data.

    If a parameter is not supported by the API, it will be skipped and a warning will be logged.
    If no valid parameters are provided, a ValueError will be raised.

    Args:
        stations (list[StationMetadata]): Stations from which to retrieve data.
        time_from (date): Start of the query interval.
        time_to (date): End of the query interval.
        parameters (list[Parameter]): Requested data parameters.
        quality (bool, optional): Whether to include quality values. Defaults to False.

    Returns:
        _GeoSphereAustriaHistoricalStationLocationData: The retrieved historical station data.
    """
    logger.info(
        f"Retrieving data for stations: {[station.name for station in stations]} from {time_from} to {time_to} for parameters: {parameters} with quality: {quality}"
    )
    station_ids = ",".join([str(station.id) for station in stations])
    mapped_parameters: set[str] = set()
    for p in parameters:
        if p in PARAMETER_MAPPING:
            mapped_parameters.add(PARAMETER_MAPPING[p])
        else:
            logger.info(
                f"Parameter {p} not supported by GeoSphere Austria API, skipping"
            )
    if len(mapped_parameters) == 0:
        raise ValueError("No valid parameters provided for GeoSphere Austria API")
    if quality:
        for p in parameters:
            if p in QUALITY_PARAMETER:
                mapped_parameters.add(QUALITY_PARAMETER[p])
            else:
                logger.info(
                    f"Quality information for parameter {p} not supported by GeoSphere Austria API, skipping"
                )
    parameters_str = ",".join(mapped_parameters)
    query_url = f"{BASE_URL}/station/historical/klima-v2-1d?station_ids={station_ids}&parameters={parameters_str}&start={time_from.isoformat()}&end={time_to.isoformat()}"
    r = requests.get(query_url)
    r.raise_for_status()
    response = r.json()
    return _GeoSphereAustriaHistoricalStationLocationData._from_api_response(
        StationGeoJSONSerializer(**response), api_parameters=mapped_parameters
    )


class _GeoSphereAustria(DataProvider):
    """GeoSphere Austria data provider implementation."""

    @staticmethod
    def get_historical_location_data(
        time_from: date,
        time_to: date,
        locations: Point | list[Point],
        parameters: list[Parameter],
        radius: float | None = None,
        quality: bool = False,
    ) -> LocationData:
        """Return historical location data for requested locations.

        Args:
            time_from (date): Start of the requested interval.
            time_to (date): End of the requested interval.
            locations (Point | list[Point]): One or more locations to query.
            parameters (list[Parameter]): Requested weather parameters.
            radius (float | None, optional): Search radius in kilometers when a single
                location is provided. Defaults to None.
            quality (bool, optional): Include quality information if available.
                Defaults to False.

        Returns:
            LocationData: Retrieved data container.

        Raises:
            ValueError: For invalid combinations of locations and radius, or if
                the location list is empty.
        """
        logger.info(
            f"Getting historical location data from GeoSphere Austria API for time range {time_from} to {time_to}, locations: {locations}, parameters: {parameters}, radius: {radius}, quality: {quality}"
        )
        if isinstance(locations, Point):
            locations = [locations]
        if len(locations) == 0:
            raise ValueError("Location list cannot be empty.")
        if radius is not None and radius < 0:
            raise ValueError("Radius cannot be negative.")
        if radius is not None and len(locations) > 1:
            raise ValueError(
                "Radius cannot be specified when multiple locations are provided."
            )
        if len(locations) == 1 and radius is None:
            stations = list(_get_closest_station(location) for location in locations)
            stations = [station for station in stations if station is not None]
            return _get_data_for_stations(
                stations, time_from, time_to, parameters=parameters, quality=quality
            )
        if len(locations) == 1 and radius is not None:
            stations = _get_stations_within_radius(locations[0], radius)
            return _get_data_for_stations(
                stations, time_from, time_to, parameters=parameters, quality=quality
            )
        if len(locations) > 1:
            stations = []
            for location in locations:
                closest_station = _get_closest_station(location)
                if closest_station is not None and closest_station not in stations:
                    stations.append(closest_station)
            return _get_data_for_stations(
                stations,
                time_from,
                time_to,
                parameters=parameters,
                quality=quality,
            )
        logger.error(
            "Invalid combination of parameters provided for GeoSphere Austria API"
        )
        raise ValueError("Invalid combination of parameters.")
