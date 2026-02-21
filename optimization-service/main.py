from fastapi import FastAPI, UploadFile, File, Query
from optimizer import optimize_model
import os

app = FastAPI()

UPLOAD_DIR = "uploads"
OPTIMIZED_DIR = "optimized"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OPTIMIZED_DIR, exist_ok=True)

@app.post("/optimize")
async def optimize(
    file: UploadFile = File(...),
    apply_pruning: bool = Query(True, description="Apply pruning to the model"),
    apply_distillation: bool = Query(True, description="Apply knowledge distillation"),
    pruning_amount: float = Query(0.3, ge=0.0, le=0.9, description="Fraction of weights to prune (0.0-0.9)")
):
    """
    Optimize a PyTorch model using pruning, knowledge distillation, and quantization
    
    Parameters:
    - file: PyTorch .pt model file
    - apply_pruning: Enable/disable pruning (default: True)
    - apply_distillation: Enable/disable knowledge distillation (default: True)
    - pruning_amount: Percentage of weights to prune, 0.0-0.9 (default: 0.3)
    """
    try:
        input_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(input_path, "wb") as f:
            f.write(await file.read())

        result = optimize_model(
            input_path, 
            OPTIMIZED_DIR,
            apply_pruning_flag=apply_pruning,
            apply_distillation_flag=apply_distillation,
            pruning_amount=pruning_amount
        )
        return result
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

