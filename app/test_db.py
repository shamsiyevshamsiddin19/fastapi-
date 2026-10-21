from .database import engine


def check_database_connection():
    try:
        with engine.connect():
            print("PostgreSQL ga muvaffaqiyatli ulandi!")
    except Exception as error:
        print(f"Ulanishda xato: {error}")


if __name__ == "__main__":
    check_database_connection()
