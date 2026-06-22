from dotenv import load_dotenv
load_dotenv()

from database.db import init_db
from ui.app import VerdictOSApp

if __name__ == '__main__':
    init_db()
    VerdictOSApp().run()
