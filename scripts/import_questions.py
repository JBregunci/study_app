import argparse
from pathlib import Path

from app.config import CATALOG_DIR, MATERIALS_DIR, QUESTIONS_DIR
from app.db import SessionLocal, init_db
from app.models import ReviewStatus
from app.services.material_import import import_materials_directory
from app.services.question_import import import_all, import_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa questões para o SQLite.")
    parser.add_argument(
        "path",
        nargs="?",
        default=str(QUESTIONS_DIR),
        help="arquivo JSON ou diretório com arquivos JSON",
    )
    parser.add_argument(
        "--status",
        choices=[status.value for status in ReviewStatus],
        default=ReviewStatus.approved.value,
        help="status padrão para questões sem review_status",
    )
    args = parser.parse_args()

    path = Path(args.path)
    init_db()
    material_report = None
    with SessionLocal() as db:
        if path.is_dir():
            report = import_all(db, path, CATALOG_DIR, ReviewStatus(args.status))
            material_report = import_materials_directory(db, MATERIALS_DIR)
        else:
            report = import_file(db, path, ReviewStatus(args.status))

    print(
        f"Questões — arquivos: {report.files} | criadas: {report.created} | "
        f"atualizadas: {report.updated} | ignoradas: {report.skipped}"
    )
    if material_report is not None:
        print(
            f"Materiais — arquivos: {material_report.files} | criados: "
            f"{material_report.created} | atualizados: {material_report.updated} | "
            f"ignorados: {material_report.skipped}"
        )
    errors = list(report.errors)
    if material_report is not None:
        errors.extend(material_report.errors)
    for error in errors:
        print(f"ERRO: {error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
