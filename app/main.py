import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles

from .config import APP_NAME, AUTO_IMPORT, BASE_DIR, CATALOG_DIR, MATERIALS_DIR, MEDIA_DIR, QUESTIONS_DIR
from .db import SessionLocal, init_db
from .models import ReviewStatus
from .routers import api, dashboard, exams, materials, practice, questions, sets, stats, topics
from .services.material_import import import_materials_directory
from .services.question_import import import_all
from .templating import templates

logger = logging.getLogger("study_app")


def create_app(run_startup: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if run_startup:
            init_db()
            if AUTO_IMPORT and QUESTIONS_DIR.exists():
                with SessionLocal() as db:
                    report = import_all(
                        db,
                        QUESTIONS_DIR,
                        CATALOG_DIR,
                        default_status=ReviewStatus.approved,
                    )
                    material_report = import_materials_directory(db, MATERIALS_DIR)
                for error in report.errors + material_report.errors:
                    logger.warning("Importação: %s", error)
                logger.info(
                    "Conteúdo importado: %s questões criadas, %s atualizadas, %s materiais",
                    report.created,
                    report.updated,
                    material_report.created + material_report.updated,
                )
        yield

    app = FastAPI(title=APP_NAME, lifespan=lifespan)
    app.mount(
        "/static",
        StaticFiles(directory=str(BASE_DIR / "app/static")),
        name="static",
    )
    app.mount(
        "/media",
        StaticFiles(directory=str(MEDIA_DIR)),
        name="media",
    )
    app.include_router(dashboard.router)
    app.include_router(questions.router)
    app.include_router(exams.router)
    app.include_router(topics.router)
    app.include_router(materials.router)
    app.include_router(practice.router)
    app.include_router(sets.router)
    app.include_router(stats.router)
    app.include_router(api.router)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if request.url.path.startswith("/api"):
            return JSONResponse(
                {"detail": exc.detail}, status_code=exc.status_code
            )
        if exc.status_code == 404:
            return templates.TemplateResponse(
                request=request,
                name="404.html",
                context={"detail": exc.detail},
                status_code=404,
            )
        return JSONResponse(
            {"detail": exc.detail}, status_code=exc.status_code
        )

    return app


app = create_app()
