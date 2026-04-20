import json
import os
from pathlib import Path
from fastapi import HTTPException
from app.modules.map_config.schemas import MapConfigRequest, MapConfigResponse

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
CONFIG_FILE = DATA_DIR / "map_config.json"


class MapConfigService:
    def get(self) -> MapConfigResponse:
        if not CONFIG_FILE.exists():
            raise HTTPException(status_code=404, detail="Map configuration not found")
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            return MapConfigResponse(**data)
        except (json.JSONDecodeError, Exception) as e:
            raise HTTPException(status_code=500, detail=f"Map configuration file is corrupted: {e}")

    def save(self, config: MapConfigRequest) -> MapConfigResponse:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        # Write atomically via temp file
        tmp_file = CONFIG_FILE.with_suffix(".tmp")
        with open(tmp_file, "w") as f:
            json.dump(config.model_dump(), f, indent=2)
        tmp_file.replace(CONFIG_FILE)
        return MapConfigResponse(**config.model_dump())
