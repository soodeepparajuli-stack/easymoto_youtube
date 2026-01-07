import os
import time

DB_PATH = os.path.join("data", "easymoto.db")

def reset():
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("Database deleted.")
        except Exception as e:
            print(f"Error deleting DB: {e}")
    else:
        print("DB not found (clean).")

if __name__ == "__main__":
    reset()
