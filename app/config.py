import os
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
QUESTIONS_DIR = DATA_DIR / "questions"
CATALOG_DIR = DATA_DIR / "catalog"
MATERIALS_DIR = DATA_DIR / "materials"
SOURCES_DIR = DATA_DIR / "sources"
MEDIA_DIR = DATA_DIR / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(os.getenv("STUDY_DB_PATH", str(DATA_DIR / "study.db")))
TIMEZONE = ZoneInfo(os.getenv("STUDY_TIMEZONE", "America/Sao_Paulo"))
AUTO_IMPORT = os.getenv("STUDY_AUTO_IMPORT", "1") != "0"
APP_NAME = "Estudo para Concursos"
