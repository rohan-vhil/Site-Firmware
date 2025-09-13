from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from RaspberryPI.controllers.rpi_controller import router as rpi_router
from sessions import engine, Base

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(rpi_router, prefix="/rpi", tags=["Raspberry Pi"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000, log_level="info")
