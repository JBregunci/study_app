from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.config import CATALOG_DIR, MATERIALS_DIR, QUESTIONS_DIR
from app.db import Base, get_db, make_engine
from app.main import create_app
from app.models import ReviewStatus
from app.services.material_import import import_materials_directory
from app.services.question_import import import_all


@dataclass
class TestEnv:
    client: TestClient
    sessions: sessionmaker


@pytest.fixture()
def env(tmp_path):
    engine = make_engine(tmp_path / "test.db")
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False
    )
    with testing_session() as db:
        report = import_all(db, QUESTIONS_DIR, CATALOG_DIR, ReviewStatus.approved)
        assert not report.errors
        material_report = import_materials_directory(db, MATERIALS_DIR)
        assert not material_report.errors

    application = create_app(run_startup=False)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    application.dependency_overrides[get_db] = override_get_db
    with TestClient(application) as client:
        yield TestEnv(client=client, sessions=testing_session)
