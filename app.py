# Render deployment entry point
# This file imports the Flask app from source.py for Render compatibility

from source import app

if __name__ == "__main__":
    app.run()
