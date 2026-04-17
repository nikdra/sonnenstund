from pydantic import BaseModel
from sonnenstund.models.quality import Quality


class _GeoSphereAustriaParameter(BaseModel):
    """Class for describing the shape of the parameter response from GeoSphere Austria

    Args:
        BaseModel (_type_): pydantic Base Model
    """

    name: str
    unit: str
    data: list[int | float]


class _GeoSphereAustriaSunHoursParameter(_GeoSphereAustriaParameter):
    @property
    def sun_minutes(self):
        return [
            h * 60 for h in self.data
        ]  # for the future (other sources?) it might be good to standardize early


class _GeoSphereAustriaSunHoursQualityParameter(_GeoSphereAustriaParameter):
    def _quality_conversion(self, val: int | float):
        if val < 10:
            return Quality.LOW
        if 10 < val < 20:
            return Quality.MEDIUM
        if 20 < val:
            return Quality.HIGH
        return Quality.UNKNOWN  # unknown quality for this source; can be null

    @property
    def quality(self):
        return [
            self._quality_conversion(v) for v in self.data
        ]  # for the future (other sources?) it might be good to standardize early


class GeoSphereAustriaParameters(BaseModel):
    """Class for defining the parameters of a geopandas request from GeoSphere Austria

    Args:
        BaseModel (_type_): pydantic Base Model
    """

    so_h: _GeoSphereAustriaSunHoursParameter
    so_h_flag: _GeoSphereAustriaSunHoursQualityParameter
