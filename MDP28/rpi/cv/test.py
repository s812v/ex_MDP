import requests
import json

# Set the URL for the detect API
detect_url = "http://127.0.0.1:5000/detect"  # Update the port if needed

# Example image file path
image_file_path = "2c947bcaf6ca4b1c37f44f9cff180d01.png"

# Prepare the image file to be sent in the POST request
files = {'image': ('example_image.png', open(image_file_path, 'rb'), 'image/jpeg')}

# Make the API call
response = requests.post(detect_url, files=files)

# Check the response
if response.status_code == 200:
    # Print the detected objects and their information
    print(response.json())
else:
    # Print the error message
    print(f"Error {response.status_code}: {response.json()}")
