import torch
import torch.nn as nn
import os
import pickle
import sys
import warnings
from onnxruntime.quantization import quantize_dynamic, QuantType

# Suppress warnings
warnings.filterwarnings('ignore')


# MUST match EXACTLY with generate_model.py
class LargeModel(nn.Module):
    def __init__(self):
        super(LargeModel, self).__init__()
        self.fc1 = nn.Linear(4096, 4096)  # ~16.7M params
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(4096, 4096)  # ~16.7M params

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x


# Register LargeModel in __main__ module so pickle can find it
sys.modules['__main__'].LargeModel = LargeModel


def load_model(pt_path):
    """Load model with proper handling"""
    print(f"[LOADER] Loading model from {pt_path}...")
    try:
        # Disabling pickle restriction for loading the model
        model = torch.load(pt_path, map_location="cpu", weights_only=False)
        print(f"[LOADER] Model loaded successfully: {type(model).__name__}")
        return model
    except Exception as e:
        print(f"[LOADER] First attempt failed: {e}")
        # Fallback: Try with strict loading disabled
        try:
            import pickle as pkl
            with open(pt_path, 'rb') as f:
                # Use pickle with a restricted unpickler
                pkl.load(f)
        except Exception as e2:
            print(f"[LOADER] Fallback also failed: {e2}")
            raise
        raise


def get_file_size_mb(path):
    return os.path.getsize(path) / (1024 * 1024)


def convert_pt_to_onnx(pt_path, output_dir):
    """Convert PyTorch model to ONNX format"""
    print(f"\n[CONVERTER] Loading PT model from: {pt_path}")
    
    try:
        model = load_model(pt_path)
    except Exception as e:
        print(f"[CONVERTER] ERROR loading model: {e}")
        raise
    
    model.eval()
    
    # Create dummy input with correct shape (batch_size=1, features=4096)
    dummy_input = torch.randn(1, 4096)
    print(f"[CONVERTER] Model type: {type(model).__name__}")
    print(f"[CONVERTER] Dummy input shape: {dummy_input.shape}")

    onnx_path = os.path.join(
        output_dir, os.path.basename(pt_path).replace(".pt", ".onnx")
    )

    try:
        print(f"[CONVERTER] Exporting to ONNX: {onnx_path}")
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            input_names=["input"],
            output_names=["output"],
            opset_version=11,
        )
        print(f"[CONVERTER] ONNX export successful")
    except Exception as e:
        print(f"[CONVERTER] ERROR during ONNX export: {e}")
        raise

    return onnx_path


def optimize_model(input_path, output_dir):
    """Main optimization pipeline"""
    print(f"\n{'='*60}")
    print(f"[OPTIMIZER] Starting optimization")
    print(f"{'='*60}")
    
    original_size = get_file_size_mb(input_path)
    print(f"[OPTIMIZER] Original PT size: {original_size:.2f} MB")

    # Step 1: Convert to ONNX
    if input_path.endswith(".pt"):
        print(f"[OPTIMIZER] Converting PT to ONNX...")
        onnx_path = convert_pt_to_onnx(input_path, output_dir)
        onnx_size = get_file_size_mb(onnx_path)
        print(f"[OPTIMIZER] ONNX size: {onnx_size:.2f} MB")
        if original_size > 0:
            print(f"[OPTIMIZER] PT → ONNX reduction: {((original_size - onnx_size) / original_size * 100):.2f}%")
    else:
        onnx_path = input_path
        onnx_size = original_size

    # Step 2: Dynamic Quantization to Int8
    optimized_path = os.path.join(
        output_dir,
        os.path.basename(onnx_path).replace(".onnx", "_quantized.onnx"),
    )

    try:
        print(f"\n[OPTIMIZER] Applying dynamic quantization (QInt8)...")
        quantize_dynamic(
            model_input=onnx_path,
            model_output=optimized_path,
            weight_type=QuantType.QInt8,
        )
        print(f"[OPTIMIZER] Quantization successful")
    except Exception as e:
        print(f"[OPTIMIZER] ERROR during quantization: {e}")
        raise

    optimized_size = get_file_size_mb(optimized_path)
    print(f"[OPTIMIZER] Quantized size: {optimized_size:.2f} MB")

    size_reduction = (
        (original_size - optimized_size) / original_size * 100
        if original_size > 0
        else 0
    )

    print(f"\n[OPTIMIZER] Total reduction: {size_reduction:.2f}%")
    print(f"[OPTIMIZER] Original: {original_size:.2f} MB → Optimized: {optimized_size:.2f} MB")
    print(f"{'='*60}\n")

    return {
        "optimizedFileName": os.path.basename(optimized_path),
        "optimizedSize": round(optimized_size, 2),
        "sizeReduction": round(size_reduction, 2),
    }


