from datetime import datetime

import torch
from ultralytics import YOLO
import cv2
import math
from django.core.cache import cache

loaded_models = {}

model_class_names = {
    "yolov8n.pt": ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "tank", "truck", "boat",
                  "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
                  "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
                  "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
                  "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
                  "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
                  "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
                  "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
                  "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
                  "teddy bear", "hair drier", "military vehicle"
                  ],
    "best3.pt": ["tank","0","1"],
    "models/best_IDF_tank.pt": ["Tank", "cars", "cake", "fish", "horse", "sheep", "cow", "elephant", "zebra", "giraffe"],
    "models/tankNZ.pt": ["tank"],
    # Add more models and their corresponding class names here
}

def load_model(model_name):
    if model_name not in loaded_models:
        model = YOLO(model_name).to(torch.device('cpu'))  # Force the model to run on CPU
        loaded_models[model_name] = model
    return loaded_models[model_name]

def video_detection(frame, model_name):
    # Load the selected YOLO model
    model = load_model(model_name)

    # Get class names for the selected model
    classNames = model_class_names.get(model_name, [])

    # Perform YOLO detection on the given frame
    results = model(frame, stream=True)

    detections = cache.get('detections', [])

    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)

            cls = int(box.cls[0].item())

            if cls >= len(classNames):
                print(f"Warning: class index {cls} is out of range for classNames")
                continue

            conf = box.conf[0].item() + 0
            if conf >= 1.0:
                conf = 0.99

            class_name = classNames[cls]

            if conf >= 0.7:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)
                label = f'{class_name} {conf:.2f}'
                t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, thickness=1)[0]
                c2 = (x1 + t_size[0], y1 - t_size[1] - 3)
                cv2.rectangle(frame, (x1, y1), c2, (255, 0, 255), -1)
                cv2.putText(frame, label, (x1, y1 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), thickness=1)

                if class_name == 'tank':
                    detections.append({'class': 'tank', 'confidence': round(conf,2),
                                       'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
    cache.set('detections', detections, timeout=300)

    return frame

cv2.destroyAllWindows()