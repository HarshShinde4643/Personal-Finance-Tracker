
from database import get_db_connection

try:
    db = get_db_connection()

    if db.is_connected():
        print("MySQL Database Connected Successfully!")

    db.close()

except Exception as error:
    print("Database Error:", repr(error))
