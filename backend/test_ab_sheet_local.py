from pathlib import Path
from app.utils.ab_sheet_inference import predict_ab_table_from_image

image_path = Path("img1.jpg")  # file in the backend folder
with image_path.open("rb") as f:
    file_bytes = f.read()

result = predict_ab_table_from_image(file_bytes)
print(result["extraction_summary"])
print(result["tables"][0]["rows"][0])