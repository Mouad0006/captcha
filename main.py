from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64
import re
import easyocr

reader = easyocr.Reader(['en'], gpu=False)

app = Flask(__name__)
CORS(app)

def base64_to_image(base64_image):
    try:
        if ',' not in base64_image:
            raise ValueError("Base64 string format is invalid")
        image_data = base64.b64decode(base64_image.split(",")[1])
        np_arr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image data - OpenCV failed to decode")
        return img
    except Exception as e:
        raise ValueError(f"Base64 decode error: {e}")

def enhance_contrast(image):
    try:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    except:
        return image  # في حالة الفشل، استخدم الصورة الأصلية

def process_image_for_numbers(image):
    try:
        results = reader.readtext(image)
        detected_text = " ".join([res[1] for res in results])
        numbers_only = re.findall(r'\d+', detected_text)
        return numbers_only
    except Exception as e:
        return []

@app.route('/ocr', methods=['POST'])
def ocr_api():
    data = request.get_json()
    if not data or 'images' not in data:
        return jsonify({"error": "المدخلات غير صحيحة. يجب تضمين مفتاح 'images'."}), 400

    images = data['images']
    if not isinstance(images, list):
        return jsonify({"error": "'images' يجب أن تكون قائمة."}), 400

    enhance = data.get('enhance_contrast', True)
    results = []

    for img_data in images:
        image_id = img_data.get('id', 'undefined')
        base64_image = img_data.get('image')

        if not base64_image:
            results.append({"id": image_id, "error": "Missing 'image'"})
            continue

        try:
            image = base64_to_image(base64_image)
            if enhance:
                image = enhance_contrast(image)

            numbers = process_image_for_numbers(image)
            results.append({
                "id": image_id,
                "number": numbers[0] if numbers else None
            })
        except Exception as e:
            results.append({
                "id": image_id,
                "error": f"Processing failed: {str(e)}"
            })

    return jsonify(results), 200

import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7777))
    app.run(host='0.0.0.0', port=port)

