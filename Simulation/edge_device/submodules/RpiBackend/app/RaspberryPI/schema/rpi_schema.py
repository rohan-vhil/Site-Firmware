from pydantic import BaseModel, Field
from typing import Annotated, List

class Device(BaseModel):
    device_type: Annotated[str, Field(min_length=3, max_length=50)]
    device_brand: Annotated[str, Field(min_length=3, max_length=50)]
    device_model_no: Annotated[str, Field(min_length=3, max_length=50)]
    device_serial_no: Annotated[str, Field(min_length=3, max_length=50)]

class DeviceConfiguration(BaseModel):
    client_codes: List[str]
    devices: List[Device]