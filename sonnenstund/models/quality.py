from enum import StrEnum, auto


class Quality(StrEnum):
    """Quality categories for weather data measurements.

    Attributes:
        HIGH: High-quality measurement.
        MEDIUM: Medium-quality measurement.
        LOW: Low-quality measurement.
        UNKNOWN: Unknown or missing quality information.
    """

    HIGH = auto()
    MEDIUM = auto()
    LOW = auto()
    UNKNOWN = auto()
