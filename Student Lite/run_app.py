import webview
import threading
from app import app

def start_flask():
    app.run(debug=False)

# Start Flask in a thread
threading.Thread(target=start_flask).start()

# Open the app in its own window
webview.create_window("Student Lite", "http://127.0.0.1:5000", width=1000, height=700)
webview.start()
