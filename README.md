[![codecov](https://codecov.io/github/nikdra/sonnenstund/branch/main/graph/badge.svg?token=BSD520ROWN)](https://codecov.io/github/nikdra/sonnenstund)
[![Tests](https://github.com/nikdra/sonnenstund/actions/workflows/tests.yaml/badge.svg?branch=main)](https://github.com/nikdra/sonnenstund/actions/workflows/tests.yaml)
[![Publish Python 🐍 distribution 📦 to PyPI and TestPyPI](https://github.com/nikdra/sonnenstund/actions/workflows/publish-to-pypi.yaml/badge.svg?branch=main)](https://github.com/nikdra/sonnenstund/actions/workflows/publish-to-pypi.yaml)
# sonnenstund
Hours of Direct Sunlight in Your Area.

The `sonnenstund` contains classes to query historical sunlight hours for a given location.

Supported regions/providers:

|Country|Provider|
|-|-|
|Austria|[GeoSphere Austria](https://data.hub.geosphere.at/)

If your location is not supported, you will get data from the closest supported region.

To run, this package requires an active internet connection.

Data is either retured as a Pandas DataFrame or a GeoPandas GeoDataFrame.

## Install

From PyPI:
```
pip install sonnenstund
```

## How to use
TODO
