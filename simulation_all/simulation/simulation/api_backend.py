from fastapi import FastAPI, Request
from typing import Dict
import uvicorn

app = FastAPI()
device_data = {}
control_commands = {}

@app.post("/log-data")
async def log_data(payload: Dict):
    device_name = payload.get("device_name")
    device_data[device_name] = payload
    print(f"[API] Data from {device_name}: {payload}")
    return {"status": "ok"}

@app.get("/control-params")
async def get_control(device: str):
    return control_commands.get(device, {})

@app.post("/control-params")
async def set_control(payload: Dict):
    device_name = payload.get("device_name")
    control_commands[device_name] = payload
    return {"status": "updated"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
