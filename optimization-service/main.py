from fastapi import FastAPI, UploadFile, File
from optimizer import optimize_model
import os

app = FastAPI()

UPLOAD_DIR = "uploads"
OPTIMIZED_DIR = "optimized"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OPTIMIZED_DIR, exist_ok=True)

@app.post("/optimize")
async def optimize(file: UploadFile = File(...)):
    try:
        input_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(input_path, "wb") as f:
            f.write(await file.read())

        result = optimize_model(input_path, OPTIMIZED_DIR)
        return result
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

