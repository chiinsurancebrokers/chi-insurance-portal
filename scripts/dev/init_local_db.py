import os
import src.database.models as m

def main():
    # Find Base
    Base = getattr(m, "Base", None)
    if Base is None:
        raise RuntimeError("models.py has no Base. Paste models.py top part so we can target the right object.")

    # Find engine (common names)
    engine = getattr(m, "engine", None)
    if engine is None:
        engine = getattr(m, "ENGINE", None)

    # If engine not found, try to build one from DATABASE_URL if create_engine exists
    if engine is None:
        create_engine = getattr(m, "create_engine", None)
        if create_engine is None:
            from sqlalchemy import create_engine as ce
            create_engine = ce
        db_url = os.getenv("DATABASE_URL", "sqlite:///data/chi_portal_local.db")
        engine = create_engine(db_url)

    Base.metadata.create_all(bind=engine)
    print("✅ Tables created.")

if __name__ == "__main__":
    main()
