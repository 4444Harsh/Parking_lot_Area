import cv2
import numpy as np
import pickle
from skimage.transform import resize


class ParkingDetector:
    def __init__(self, model_path):
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

    def get_parking_spots(self, mask):
        """Get parking spots from mask image"""
        # Convert to grayscale if needed
        if len(mask.shape) == 3:
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

        # Threshold to create binary image
        _, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        spots = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            spots.append([x, y, w, h])

        return spots

    def check_spot_empty(self, img, spot):
        """Check if parking spot is empty"""
        x, y, w, h = spot

        # Extract spot image
        spot_img = img[y:y + h, x:x + w]

        # Skip if spot is invalid
        if spot_img.size == 0 or w < 10 or h < 10:
            return False

        # Convert to 3 channels if needed
        if len(spot_img.shape) == 2:
            spot_img = cv2.cvtColor(spot_img, cv2.COLOR_GRAY2BGR)

        # Resize and predict
        spot_resized = resize(spot_img, (15, 15, 3), anti_aliasing=True)
        flat_data = spot_resized.flatten().reshape(1, -1)
        return self.model.predict(flat_data)[0] == 0

    def process_frame(self, frame, mask):
        """Process frame with mask"""
        spots = self.get_parking_spots(mask)
        spot_status = []

        for spot in spots:
            is_empty = self.check_spot_empty(frame, spot)
            spot_status.append(is_empty)
            color = (0, 255, 0) if is_empty else (0, 0, 255)
            cv2.rectangle(frame, (spot[0], spot[1]),
                          (spot[0] + spot[2], spot[1] + spot[3]), color, 2)

        # Display count
        available = sum(spot_status)
        total = len(spots)
        cv2.putText(frame, f"Available: {available}/{total}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        return frame