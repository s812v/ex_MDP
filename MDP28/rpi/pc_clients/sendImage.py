from flask import Flask, Response, send_file
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import base64
import time
from flask_cors import CORS  # Import the CORS module


app = Flask(__name__)
CORS(app)
# Folder to monitor for changes
folder_to_watch = '/Users/chester/Downloads/inference_server_2/predictions'

# Function to encode image to base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
    return encoded_string

# Function to send the latest PNG file in base64 format to the frontend
CORS(app)
def send_latest_png_base64():
    files = [os.path.join(folder_to_watch, f) for f in os.listdir(folder_to_watch) if f.endswith('.jpg')]
    
    if files:
        # print('testing')
        latest_png = max(files, key=os.path.getctime)
        image_path = os.path.join(folder_to_watch, latest_png)
        # print('testing')
        base64_image = encode_image_to_base64(image_path)
	
        return base64_image
    else:
        return None

# Watchdog event handler to detect changes in the folder
CORS(app)
class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith('.jpg'):
        #     print("New PNG file created:", event.src_path)
            time.sleep(1)  # Adding a delay to ensure file is fully written
            app.config['latest_png'] = event.src_path



# Start the watchdog observer
observer = Observer()
observer.schedule(MyHandler(), folder_to_watch, recursive=False)
observer.start()

# SSE route to continuously stream updates to the frontend
CORS(app)
@app.route('/stream_latest_png_base64')
def stream_latest_png_base64():
    def generate():
        while True:
            latest_png_base64 = send_latest_png_base64()
        #     print('test')
            if latest_png_base64:
                # print('test')

                yield f"data: {latest_png_base64}\n\n"
            time.sleep(1)  # Adjust the delay as needed
    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True)
