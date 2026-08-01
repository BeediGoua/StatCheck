from src.db.database import engine
from sqlalchemy import text

def reset_db():
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public;"))
        conn.commit()
    print("Database schema reset successfully.")

if __name__ == "__main__":
    reset_db()
