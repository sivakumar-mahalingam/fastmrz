"""Read the Machine Readable Zone (MRZ) of passports, ID cards and visas."""
from .fastmrz import FastMRZ, InputData, InputType, MRZDetails

__version__ = "3.0.0"
__all__ = ["FastMRZ", "InputData", "InputType", "MRZDetails"]
