from ultralytics import YOLO

class AIModule:

    def __init__(self):
        self.model1 = None
        self.model2 = None

        self.MM_PER_PIXEL = 0.5
        self.FINE_LIMIT_MM = 20
        self.MEDIUM_LIMIT_MM = 50
        self.OVERSIZE_LIMIT_MM = 50


    def load_model1(self):
        if self.model1 is None:
            self.model1 = YOLO("best.pt")


    def load_model2(self):
        if self.model2 is None:
            self.model2 = YOLO("best2.pt")


    def predict(self, image):

        self.load_model1()
        results1 = self.model1(image)

        self.load_model2()
        results2 = self.model2(image)

        results = list(results1) + list(results2)

        detections = []

        for result in results:
            if result.boxes is not None:
                for box in result.boxes:

                    cls_id = int(box.cls.item())
                    conf = float(box.conf.item())

                    label = result.names[cls_id]

                    detections.append({
                        "class": label,
                        "confidence": round(conf, 2),
                        "bbox": box.xyxy.tolist()
                    })

        return detections
