from ultralytics import YOLO


class AIModule:
    def __init__(self):
        # Load trained YOLO model
        self.ai_model = YOLO("best.pt")

        # -----------------------------
        # Calibration (VERY IMPORTANT)
        # -----------------------------
        # Define how many millimeters 1 pixel represents
        # You must calibrate this based on camera setup
        self.MM_PER_PIXEL = 0.5   # Example: 1 pixel = 0.5 mm

        # -----------------------------
        # Industrial Size Thresholds (mm)
        # -----------------------------
        self.FINE_LIMIT_MM = 20       # <20 mm
        self.MEDIUM_LIMIT_MM = 50     # 20–50 mm
        self.OVERSIZE_LIMIT_MM = 50   # >50 mm


    def predict(self, image):

        results = self.ai_model(image)

        detections = []

        for result in results:
            if result.boxes is not None:
                for box in result.boxes:

                    # -----------------------------
                    # Class & Confidence
                    # -----------------------------
                    cls_id = int(box.cls.item())
                    conf = float(box.conf.item())
                    label = self.ai_model.names[cls_id]

                    # -----------------------------
                    # Bounding Box
                    # -----------------------------
                    x1, y1, x2, y2 = box.xyxy[0]

                    width_pixels = float(x2 - x1)
                    height_pixels = float(y2 - y1)

                    # -----------------------------
                    # Pixel → Millimeter Conversion
                    # -----------------------------
                    width_mm = width_pixels * self.MM_PER_PIXEL
                    height_mm = height_pixels * self.MM_PER_PIXEL

                    # -----------------------------
                    # Granulometry Classification (mm based)
                    # -----------------------------
                    if width_mm < self.FINE_LIMIT_MM:
                        size_category = "Fine"
                    elif width_mm < self.MEDIUM_LIMIT_MM:
                        size_category = "Medium"
                    else:
                        size_category = "Oversize"

                    oversize_flag = width_mm > self.OVERSIZE_LIMIT_MM

                    # -----------------------------
                    # Store Detection
                    # -----------------------------
                    detections.append({
                        "class": label,
                        "confidence": round(conf, 2),

                        "width_pixels": round(width_pixels, 2),
                        "height_pixels": round(height_pixels, 2),

                        "width_mm": round(width_mm, 2),
                        "height_mm": round(height_mm, 2),

                        "size_category": size_category,
                        "oversize": oversize_flag,

                        "bbox": box.xyxy.tolist()
                    })

        return detections