import os
import subprocess
import sys
import time
import webbrowser
from threading import Thread

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    # Delete old database
    if os.path.exists("finance.db"):
        os.remove("finance.db")
    
    # Start browser thread
    Thread(target=open_browser, daemon=True).start()
    
    # Run the app
    from app import app
    app.run(debug=False, host="0.0.0.0", port=5000)