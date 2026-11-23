from sqlalchemy import text

from app.db import engine, init_db


def column_names(connection, table: str) -> set[str]:
    rows = connection.execute(text(f"PRAGMA table_info({table})")).all()
    return {row[1] for row in rows}


def main() -> None:
    init_db()
    with engine.begin() as connection:
        exam_columns = column_names(connection, "exams")
        if "agency" not in exam_columns:
            connection.execute(
                text(
                    "ALTER TABLE exams ADD COLUMN agency VARCHAR(120) "
                    "NOT NULL DEFAULT ''"
                )
            )
        if "contest_key" not in exam_columns:
            connection.execute(
                text(
                    "ALTER TABLE exams ADD COLUMN contest_key VARCHAR(160) "
                    "NOT NULL DEFAULT ''"
                )
            )

        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS question_exams (
                    question_id INTEGER NOT NULL,
                    exam_id INTEGER NOT NULL,
                    PRIMARY KEY (question_id, exam_id),
                    FOREIGN KEY (question_id) REFERENCES questions(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                        ON DELETE CASCADE
                )
                """
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_exams_agency ON exams (agency)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_exams_contest_key ON exams (contest_key)"
            )
        )
        connection.execute(
            text(
                """
                INSERT OR IGNORE INTO question_exams (question_id, exam_id)
                SELECT id, exam_id FROM questions WHERE exam_id IS NOT NULL
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE exams
                SET agency = 'BACEN', contest_key = 'bacen-2024'
                WHERE slug IN (
                    'bacen-2024-analista-economia-financas',
                    'bacen-2024-analista-tecnologia-informacao'
                )
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE exams
                SET agency = 'DEMO', contest_key = 'demo-2026'
                WHERE slug = 'demo-2026'
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS app_meta (
                    key VARCHAR(80) PRIMARY KEY,
                    value VARCHAR(240) NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO app_meta (key, value)
                VALUES ('schema_version', '2')
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """
            )
        )
    print("Migração aplicada com sucesso. Schema versão 2.")


if __name__ == "__main__":
    main()
