import sonnenstund.data.providers.geosphereaustria as geosphere_austria


def test_stations():
    stations = geosphere_austria._GeosphereAustria()._stations
    assert len(stations) > 0
    pass
