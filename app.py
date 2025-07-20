from flask import Flask, render_template, request
import os
from werkzeug.utils import secure_filename
import cv2
from parking_detector import ParkingDetector

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MASK_FOLDER'] = 'static/masks'
app.config['RESULT_FOLDER'] = 'static/results'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Initialize detector
detector = ParkingDetector("model.p")


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Check if files were uploaded
        if 'parking_image' not in request.files or 'mask_image' not in request.files:
            return render_template("index.html", error="Both images are required")

        parking_file = request.files['parking_image']
        mask_file = request.files['mask_image']

        # Validate files
        if parking_file.filename == '' or mask_file.filename == '':
            return render_template("index.html", error="No selected file")

        if parking_file and allowed_file(parking_file.filename) and mask_file and allowed_file(mask_file.filename):
            try:
                # Save uploaded files
                parking_filename = secure_filename(parking_file.filename)
                mask_filename = secure_filename(mask_file.filename)

                parking_path = os.path.join(app.config['UPLOAD_FOLDER'], parking_filename)
                mask_path = os.path.join(app.config['MASK_FOLDER'], mask_filename)

                parking_file.save(parking_path)
                mask_file.save(mask_path)

                # Process images
                parking_img = cv2.imread(parking_path)
                mask_img = cv2.imread(mask_path)

                if parking_img is None or mask_img is None:
                    return render_template("index.html", error="Invalid image file(s)")

                # Process the frame
                result_img = detector.process_frame(parking_img, mask_img)

                # Save result
                result_filename = f"result_{parking_filename}"
                result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)
                cv2.imwrite(result_path, result_img)

                return render_template("index.html",
                                       parking_image=parking_filename,
                                       mask_image=mask_filename,
                                       result_image=result_filename)

            except Exception as e:
                return render_template("index.html", error=str(e))

    return render_template("index.html")


if __name__ == "__main__":
    # Create folders if they don't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['MASK_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)
    app.run(debug=True)