import sonnenstund.data.providers.geosphereaustria as geosphere_austria
from datetime import date, datetime
from shapely.geometry import Point
import pytest
from zoneinfo import ZoneInfo
from sonnenstund.models.geosphereaustria.model import (
    StationMetadata,
    StationMetadataType,
    Bundesland,
)
from sonnenstund.data import Parameter

# TODO modify tests to check for nan values
# TODO modify tests to check if the column names are correct (mostly for the quality parameters)


@pytest.fixture
def stations() -> list[StationMetadata]:
    stations = [
        StationMetadata(
            id=105,
            name="Test Station 1",
            lat=48.24861,
            lon=16.35639,
            valid_from=datetime.combine(
                date(2020, 1, 1), datetime.min.time(), ZoneInfo("Europe/Vienna")
            ),
            valid_to=datetime.combine(
                date(2020, 1, 31), datetime.min.time(), ZoneInfo("Europe/Vienna")
            ),
            group_id=None,
            state=None,
            altitude=None,
            has_sunshine=None,
            has_global_radiation=None,
            is_active=True,
            type=StationMetadataType.INDIVIDUAL,
        ),
        StationMetadata(
            id=106,
            name="Test Station 2",
            lat=48.20694,
            lon=16.22944,
            valid_from=datetime.combine(
                date(2020, 1, 1), datetime.min.time(), ZoneInfo("Europe/Vienna")
            ),
            valid_to=datetime.combine(
                date(2020, 1, 31), datetime.min.time(), ZoneInfo("Europe/Vienna")
            ),
            group_id=None,
            state=None,
            altitude=None,
            has_sunshine=None,
            has_global_radiation=None,
            is_active=True,
            type=StationMetadataType.INDIVIDUAL,
        ),
    ]
    return stations


@pytest.fixture
def location() -> Point:
    return Point(16.35639, 48.24861)


@pytest.fixture()
def locations() -> list[Point]:
    return [Point(16.35639, 48.24861), Point(16.41944, 48.12500)]


@pytest.fixture()
def non_station_location() -> Point:
    return Point(16.366951, 48.248621)


def test_stations():
    stations = geosphere_austria._stations()
    assert len(stations) > 0


def test_closest_station(location: Point):
    station = geosphere_austria._get_closest_station(location)
    assert station is not None
    assert station.name == "Wien Hohe Warte"


def test_closest_station_non_station_location(non_station_location: Point):
    station = geosphere_austria._get_closest_station(non_station_location)
    assert station is not None
    assert station.name == "Wien Hohe Warte"


def test_stations_within_radius(location: Point):
    stations = geosphere_austria._get_stations_within_radius(location, 5)
    assert len(stations) == 2
    assert all(station.state == Bundesland.Wien for station in stations)
    pass


def test_get_data_for_stations_multiple(stations: list[StationMetadata]):
    data = geosphere_austria._get_data_for_stations(
        stations,
        datetime.combine(date(2020, 1, 1), datetime.min.time()),
        datetime.combine(date(2020, 1, 31), datetime.min.time()),
        [Parameter.SUN_HOURS],
    )
    print(data.df)
    assert len(data.df) == 62
    assert ["date", "geometry", "sun_hours"] == list(data.df.columns)
    pass


def test_get_data_for_stations_single(stations: list[StationMetadata]):
    station = stations[0]
    data = geosphere_austria._get_data_for_stations(
        [station],
        datetime.combine(date(2020, 1, 1), datetime.min.time()),
        datetime.combine(date(2020, 1, 31), datetime.min.time()),
        [Parameter.SUN_HOURS],
    )
    assert len(data.df) > 0
    assert ["date", "geometry", "sun_hours"] == list(data.df.columns)
    print(data.df)
    pass


def test_get_historical_location_data(location: Point):
    data = geosphere_austria._GeoSphereAustria.get_historical_location_data(
        datetime.combine(date(2020, 1, 1), datetime.min.time()),
        datetime.combine(date(2020, 1, 31), datetime.min.time()),
        location,
        parameters=[Parameter.SUN_HOURS],
    )
    assert len(data.df) == 31
    assert ["date", "geometry", "sun_hours"] == list(data.df.columns)
    pass


def test_get_historical_location_data_quality(location: Point):
    data = geosphere_austria._GeoSphereAustria.get_historical_location_data(
        datetime.combine(date(2020, 1, 1), datetime.min.time()),
        datetime.combine(date(2020, 1, 31), datetime.min.time()),
        location,
        parameters=[Parameter.SUN_HOURS],
        quality=True,
    )
    assert len(data.df) == 31
    assert ["date", "geometry", "sun_hours", "sun_hours_quality"] == list(
        data.df.columns
    )
    pass


def test_get_historical_location_data_multiple(locations: list[Point]):
    data = geosphere_austria._GeoSphereAustria.get_historical_location_data(
        datetime.combine(date(2020, 1, 1), datetime.min.time()),
        datetime.combine(date(2020, 1, 31), datetime.min.time()),
        locations,
        parameters=[Parameter.SUN_HOURS],
    )
    assert len(data.df) == 62
    assert ["date", "geometry", "sun_hours"] == list(data.df.columns)
    pass


def test_get_historical_location_data_multiple_quality(locations: list[Point]):
    data = geosphere_austria._GeoSphereAustria.get_historical_location_data(
        datetime.combine(date(2020, 1, 1), datetime.min.time()),
        datetime.combine(date(2020, 1, 31), datetime.min.time()),
        locations,
        parameters=[Parameter.SUN_HOURS],
        quality=True,
    )
    assert len(data.df) == 62
    assert ["date", "geometry", "sun_hours", "sun_hours_quality"] == list(
        data.df.columns
    )
    pass


def test_get_historical_location_data_invalid_radius():
    try:
        geosphere_austria._GeoSphereAustria.get_historical_location_data(
            datetime.combine(date(2020, 1, 1), datetime.min.time()),
            datetime.combine(date(2020, 1, 31), datetime.min.time()),
            Point(0, 0),
            radius=-1,
            parameters=[Parameter.SUN_HOURS],
        )
    except ValueError as e:
        assert str(e) == "Radius cannot be negative."
    else:
        assert False, "Expected ValueError was not raised."


def test_get_historical_location_data_radius_with_multiple_locations():
    try:
        geosphere_austria._GeoSphereAustria.get_historical_location_data(
            date(2020, 1, 1),
            date(2020, 1, 31),
            [Point(0, 0), Point(1, 1)],
            radius=5,
            parameters=[Parameter.SUN_HOURS],
        )
    except ValueError as e:
        assert (
            str(e) == "Radius cannot be specified when multiple locations are provided."
        )
    else:
        assert False, "Expected ValueError was not raised."


def test_get_historical_location_data_empty_locations():
    try:
        geosphere_austria._GeoSphereAustria.get_historical_location_data(
            date(2020, 1, 1),
            date(2020, 1, 31),
            [],
            radius=100,
            parameters=[Parameter.SUN_HOURS],
        )
    except ValueError as e:
        assert str(e) == "Location list cannot be empty."
    else:
        assert False, "Expected ValueError was not raised."


def test_get_historical_location_data_single_location_with_radius(location: Point):
    data = geosphere_austria._GeoSphereAustria.get_historical_location_data(
        datetime.combine(date(2020, 1, 1), datetime.min.time()),
        datetime.combine(date(2020, 1, 31), datetime.min.time()),
        location,
        radius=5,
        parameters=[Parameter.SUN_HOURS],
    )
    assert len(data.df) == 62
    assert ["date", "geometry", "sun_hours"] == list(data.df.columns)
    pass


def test_get_historical_location_data_single_location_with_radius_quality(
    location: Point,
):
    data = geosphere_austria._GeoSphereAustria.get_historical_location_data(
        datetime.combine(date(2020, 1, 1), datetime.min.time()),
        datetime.combine(date(2020, 1, 31), datetime.min.time()),
        location,
        radius=5,
        parameters=[Parameter.SUN_HOURS],
        quality=True,
    )
    assert len(data.df) == 62
    assert ["date", "geometry", "sun_hours", "sun_hours_quality"] == list(
        data.df.columns
    )
    pass
