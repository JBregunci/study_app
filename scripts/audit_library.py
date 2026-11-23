from app.config import CATALOG_DIR, MATERIALS_DIR, QUESTIONS_DIR
from app.db import SessionLocal, init_db
from app.services.audit import audit_database, audit_sources, print_report


def main() -> int:
    init_db()
    with SessionLocal() as db:
        database_report = audit_database(db)
    source_report = audit_sources(QUESTIONS_DIR, CATALOG_DIR, MATERIALS_DIR)

    print_report(database_report)
    print()
    print_report(source_report)

    return 0 if database_report.ok and source_report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
