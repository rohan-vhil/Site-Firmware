from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent


def get_secret_local():
    env_dict = {}
    with open(BASE_DIR / '.env', "r") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                if key and value:
                    env_dict[key] = value
    return env_dict


class Settings:

    env_variables = get_secret_local()
    
    DB_USERNAME = env_variables["DB_USERNAME"]
    DB_PASSWORD = env_variables["DB_PASSWORD"]
    DB_HOST = env_variables["DB_HOST"]
    DB_PORT = env_variables["DB_PORT"]
    DB_NAME = env_variables["DB_NAME"]
    JSON_DIR = BASE_DIR / "json_files"


settings = Settings()