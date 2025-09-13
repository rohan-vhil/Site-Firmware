from itertools import product
from RaspberryPI.models.rpi_models import MasterDevices, ClientCodes
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from settings import settings
from sessions import get_psql
import json
from RaspberryPI.services.rpi_services import (
    query_master_devices,
    update_installer_cfg,
    save_as_json,
    save_as_list
)

router = APIRouter()

@router.get("/client-codes")
def get_client_codes(db: Session = Depends(get_psql)):
    try:
        client_codes = [code[0] for code in db.query(ClientCodes.client_code).all()]
        return JSONResponse(
            content={"client_codes": client_codes},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"An error occurred: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@router.post("/add-client-code")
def add_client_code(client_code: str, db: Session = Depends(get_psql)):
    try:
        new_client_code = ClientCodes(client_code=client_code)
        db.add(new_client_code)
        db.commit()
        return JSONResponse(
            content={"message": "Client code added successfully"},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"An error occurred: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@router.get("/device-types")
def get_distinct_device_types(db: Session = Depends(get_psql)):
    try:
        distinct_device_types = db.query(MasterDevices.device_type).distinct().all()
        return JSONResponse(
            content={"device_types": [device_type[0] for device_type in distinct_device_types]},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"An error occurred: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@router.get("/device-brands/{device_type}")
def get_distinct_brands(device_type: str, db: Session = Depends(get_psql)):
    try:
        distinct_brands = db.query(MasterDevices.device_brand).filter(MasterDevices.device_type == device_type).distinct().all()
        return JSONResponse(
            content={"device_brands": [model[0] for model in distinct_brands]},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"An error occurred: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@router.get("/device-models/{device_type}/{device_brand}")
def get_distinct_model(device_type: str, device_brand: str, db: Session = Depends(get_psql)):
    try:
        distinct_model = db.query(MasterDevices.device_model_no).filter(MasterDevices.device_type == device_type, MasterDevices.device_brand == device_brand).distinct().all()
        return JSONResponse(
            content={"device_models": [model[0] for model in distinct_model]},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"An error occurred: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@router.get("/installed-devices")
def get_installed_devices():
    try:
        with open(f"{settings.JSON_DIR}/installer_cfg.json", "r") as file:
            devices = json.load(file)
        return JSONResponse(
            content={"devices": devices},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"An error occurred: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@router.post("/update-installer-cfg")
def update_installer_cfg_controller(payload: dict):
    try:
        with open(f"{settings.JSON_DIR}/installer_cfg.json", "w") as file:
            json.dump(payload, file, indent=4)
        return JSONResponse(
            content={"message": "Configuration saved successfully"},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"An error occurred: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@router.post("/internet-config")
def internet_config_controller(payload: dict):
    try:
        save_as_list(payload, f"{settings.JSON_DIR}/internet-config.json")
        return JSONResponse(
            content={"message": "Configuration saved successfully"},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"An error occurred: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@router.post("/device-config")
def devices_config_controller(
    payload: dict,
    db_psql: Session = Depends(get_psql)
):
    devices = payload["devices"]
    client_codes = payload["client_codes"]
    project_code = payload["project_code"]
    try:
        masterdevices = query_master_devices(devices, db_psql)
        
        device_modbus_address = {}
        device_fault_codes = {}

        for row in masterdevices:
            device_modbus_address[row.device_model_no] = row.device_modbus_addresses
            device_fault_codes[row.device_model_no] = row.device_fault_codes
        
        all_project_devices = [
            {
                "project_code": project_code_item,
                "client_code": client_code,
                "device_id": device["device_id"],
                "device_type": device["device_type"],
                "device_brand": device["device_brand"],
                "device_model_no": device["part_num"],
                "device_serial_no": device["device_serial_no"]
            }
            for client_code, project_code_item in product(client_codes, [project_code])
            for device in devices
        ]

        save_as_json(device_modbus_address, f"{settings.JSON_DIR}/mappings.json")
        save_as_json(device_fault_codes, f"{settings.JSON_DIR}/fault_codes.json")
        save_as_list(all_project_devices, f"{settings.JSON_DIR}/project_devices.json")
        update_installer_cfg(devices, f"{settings.JSON_DIR}/installer_cfg.json")
        
        return JSONResponse(
            content={
                "message": "Device configuration saved successfully"
            },
            status_code=status.HTTP_200_OK
        )

    except Exception as e:
        return JSONResponse(
            content={"error": f"An error occured: {e}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )