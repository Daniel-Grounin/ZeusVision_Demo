from datetime import datetime
from ultralytics import YOLO
import cv2
import math
from django.core.cache import cache

# Load the YOLO model once globally
model = YOLO("../ZeusVision_Demo/models/best_IDF_tank.pt")
# classNames = ["0"]  # Ensure the class names match your trained model
classNames = ["Cow", "Hamer", "Nagmash", "Person", "Tender", "Tank"]  # Ensure the class names match your trained model

def video_detection(frame):
    # Perform YOLO detection on the given frame
    results = model(frame, stream=True)

    for r in results:
        boxes = r.boxes
        for box in boxes:
            # Extract coordinates and ensure they are within the frame dimensions
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

            # Ensure the coordinates are within the frame boundaries
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)

            conf = box.conf[0]
            cls = int(box.cls[0])
            class_name = classNames[cls]

            if conf >= 0.8:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)
                label = f'{class_name} {conf:.2f}'
                t_size = cv2.getTextSize(label, 0, fontScale=1, thickness=2)[0]
                c2 = x1 + t_size[0], y1 - t_size[1] - 3
                cv2.rectangle(frame, (x1, y1), c2, [255, 0, 255], -1, cv2.LINE_AA)  # filled
                cv2.putText(frame, label, (x1, y1 - 2), 0, 1, [255, 255, 255], thickness=1, lineType=cv2.LINE_AA)

                # Cache the detection if it's a 'tank'
                if class_name == 'Tank':
                    detections = cache.get('detections', [])
                    detections.append({'class': 'tank', 'confidence': conf,
                                       'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
                    cache.set('detections', detections, timeout=300)  # Adjust timeout as needed

    return frame

cv2.destroyAllWindows()
