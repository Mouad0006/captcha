from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64
import re
import easyocr
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)  # غيّر origins لو تريد تقييد الدومين

# تحميل موديل easyocr مرة واحدة (الأهم)
reader = easyocr.Reader(['en'], gpu=False)

def base64_to_image(base64_image):
    # يدعم الصور المرفقة مع "data:image/..." أو بدونها
    try:
        if ',' in base64_image:
            image_data = base64.b64decode(base64_image.split(",")[1])
        else:
            image_data = base64.b64decode(base64_image)
        np_arr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image data - OpenCV failed to decode")
        return img
    except Exception as e:
        raise ValueError(f"Base64 decode error: {e}")

@app.route("/ocr", methods=["POST"])
def ocr():
    data = request.get_json()
    if not data or 'images' not in data:
        return jsonify({"error": "No images sent"}), 400

    images = data['images']
    if len(images) == 0:
        return jsonify({"error": "No images sent"}), 400

    results = []
    for img_b64 in images:
        try:
            img = base64_to_image(img_b64)
            # هنا يمكنك وضع تحسين contrast إذا أردت
            # img = enhance_contrast(img)
            text_list = reader.readtext(img, detail=0)
            text = " ".join(text_list)
            results.append(text)
        except Exception as e:
            results.append(f"Error: {str(e)}")
    return jsonify({"results": results})

@app.route("/", methods=["GET"])
def home():
    return "Captcha OCR Server is running!", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7777))
    app.run(host='0.0.0.0', port=port)
