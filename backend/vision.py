import os
import io
import json
import pickle
import datetime
import base64
import tempfile
import numpy as np

try:
    import cv2
    cv2_available = True
except ImportError:
    cv2_available = False

try:
    import face_recognition
    face_recognition_available = True
except ImportError:
    face_recognition_available = False

try:
    from ultralytics import YOLO
    yolo_available = True
except ImportError:
    yolo_available = False

try:
    from PIL import Image, ImageGrab
    pil_available = True
except ImportError:
    pil_available = False

try:
    import pyautogui
    pyautogui_available = True
except ImportError:
    pyautogui_available = False

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
gemini_client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except ImportError:
        gemini_client = None

FACES_DIR = os.path.join(os.path.dirname(__file__), "faces")
os.makedirs(FACES_DIR, exist_ok=True)

YOLO_MODEL = None
if yolo_available:
    try:
        YOLO_MODEL = YOLO("yolov8n.pt")
    except Exception:
        YOLO_MODEL = None

COCO_WEAPONS = {"knife", "gun", "pistol", "rifle", "shotgun", "sword", "axe", "weapon",
                "baseball bat", "hammer", "screwdriver"}

def _bytes_to_cv2(image_bytes: bytes):
    arr = np.frombuffer(image_bytes, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)

def _cv2_to_bytes(frame):
    _, buf = cv2.imencode(".jpg", frame)
    return buf.tobytes()

def register_face(name: str, image_bytes: bytes):
    if not face_recognition_available:
        return {"error": "face_recognition module not available"}
    if not cv2_available:
        return {"error": "OpenCV module not available"}
    try:
        img = _bytes_to_cv2(image_bytes)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
        if not encodings:
            return {"error": "No face detected in the image"}
        data = {"name": name, "encoding": encodings[0].tolist(), "registered": datetime.datetime.now().isoformat()}
        path = os.path.join(FACES_DIR, f"{name.replace(' ', '_').lower()}.pkl")
        with open(path, "wb") as f:
            pickle.dump(data, f)
        return {"success": True, "name": name, "faces_registered": len(os.listdir(FACES_DIR))}
    except Exception as e:
        return {"error": str(e)}

def _load_faces():
    faces = []
    for fname in os.listdir(FACES_DIR):
        if fname.endswith(".pkl"):
            try:
                with open(os.path.join(FACES_DIR, fname), "rb") as f:
                    data = pickle.load(f)
                    faces.append(data)
            except Exception:
                continue
    return faces

def identify_faces(image_bytes: bytes):
    if not face_recognition_available:
        return {"error": "face_recognition module not available"}
    if not cv2_available:
        return {"error": "OpenCV module not available"}
    try:
        stored = _load_faces()
        if not stored:
            return {"error": "No registered faces found"}
        img = _bytes_to_cv2(image_bytes)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
        if not encodings:
            return []
        results = []
        for encoding in encodings:
            best_name = "unknown"
            best_dist = float("inf")
            for face_data in stored:
                dist = np.linalg.norm(encoding - np.array(face_data["encoding"]))
                if dist < best_dist:
                    best_dist = dist
                    best_name = face_data["name"]
            confidence = max(0, min(100, round((1 - best_dist / 0.6) * 100, 1))) if best_dist < 0.6 else 0
            if confidence > 0:
                results.append({"name": best_name, "confidence": confidence})
        return results if results else [{"name": "unknown", "confidence": 0}]
    except Exception as e:
        return {"error": str(e)}

def detect_objects(image_bytes: bytes):
    if not cv2_available:
        return {"error": "OpenCV module not available"}
    if not YOLO_MODEL:
        return {"error": "YOLOv8 model not loaded"}
    try:
        img = _bytes_to_cv2(image_bytes)
        results = YOLO_MODEL(img, verbose=False)
        detections = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                label = result.names[cls_id]
                confidence = round(float(box.conf[0]) * 100, 1)
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
                detections.append({
                    "label": label,
                    "confidence": confidence,
                    "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)]
                })
        return detections
    except Exception as e:
        return {"error": str(e)}

def analyze_scene(image_bytes: bytes):
    if not gemini_client:
        return {"error": "Gemini API key not configured"}
    try:
        from google.genai import types
        img = _bytes_to_cv2(image_bytes)
        _, jpeg = cv2.imencode(".jpg", img)
        img_bytes = jpeg.tobytes()
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                "Describe this scene in detail. What do you see? Mention people, objects, lighting, environment, and any notable activity. Be concise but thorough.",
                types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
            ],
        )
        return {"description": response.text}
    except Exception as e:
        return {"error": str(e)}

def check_threat(objects: list):
    if not isinstance(objects, list):
        return {"error": "Invalid input: expected list of objects"}
    for obj in objects:
        label = obj.get("label", "").lower().strip()
        if label in COCO_WEAPONS or any(w in label for w in COCO_WEAPONS):
            return {"threat": True, "object": label, "confidence": obj.get("confidence", 0)}
    return {"threat": False, "object": None, "confidence": 0}

def read_screen():
    if not pyautogui_available:
        return {"error": "pyautogui module not available"}
    if not gemini_client:
        return {"error": "Gemini API key not configured"}
    try:
        from google.genai import types
        screenshot = pyautogui.screenshot()
        buf = io.BytesIO()
        screenshot.save(buf, format="PNG")
        img_bytes = buf.getvalue()
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                "Describe what is visible on this computer screen. What application or website is open? What content is displayed? Be concise.",
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
            ],
        )
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        b64 = base64.b64encode(buffered.getvalue()).decode()
        return {
            "description": response.text,
            "base64": b64,
            "width": screenshot.width,
            "height": screenshot.height,
            "timestamp": datetime.datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}
