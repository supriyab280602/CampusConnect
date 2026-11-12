import os
from app import create_app
from config import Config

app = create_app()

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=Config.PORT, debug=debug_mode)
