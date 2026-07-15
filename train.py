from ultralytics import YOLO

model=YOLO("yolo11m.pt")

model.train(data= "dataset_cutsom.yaml", imgsz=640, 
            batch=8, epochs=100, workers=1, device="cpu")