from sessions import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

class MasterDevices(Base):
    __tablename__ = 'masterdevices'
    master_device_id = Column(Integer, primary_key=True, autoincrement=True)
    device_type = Column(String(255), nullable=False)
    device_brand = Column(String(255), nullable=False)
    device_model_no = Column(String(255), nullable=False)
    device_specifications = Column(JSONB, nullable=False)
    device_modbus_addresses = Column(JSONB, nullable=False)
    device_fault_codes = Column(JSONB, nullable=False)

class ClientCodes(Base):
    __tablename__ = 'clientcodes'
    client_code_id = Column(Integer, primary_key=True, autoincrement=True)
    client_code = Column(String(255), nullable=False)