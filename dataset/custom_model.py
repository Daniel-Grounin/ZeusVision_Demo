from ultralytics import YOLO

model = YOLO("../yolov8n.pt")

model.train(data="../dataset/data.yaml",epochs=2)
