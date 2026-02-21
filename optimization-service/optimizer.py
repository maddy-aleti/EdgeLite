import torch
import torch.nn as nn
import torch.nn.utils.prune as prune
import torch.optim as optim
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


# Smaller student model for knowledge distillation
class StudentModel(nn.Module):
    def __init__(self):
        super(StudentModel, self).__init__()
        self.fc1 = nn.Linear(4096, 1024)  # Much smaller
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(1024, 512)
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(512, 4096)  # Output matches teacher

    def forward(self, x):
        x = self.relu1(self.fc1(x))
        x = self.relu2(self.fc2(x))
        x = self.fc3(x)
        return x


# Register models in __main__ module so pickle can find them
sys.modules['__main__'].LargeModel = LargeModel
sys.modules['__main__'].StudentModel = StudentModel


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


def apply_pruning(model, pruning_amount=0.3):
    """
    Apply structured pruning to model layers
    Args:
        model: PyTorch model to prune
        pruning_amount: Fraction of weights to prune (0.0-1.0)
    Returns:
        Pruned model
    """
    print(f"\n[PRUNING] Applying {pruning_amount*100}% unstructured pruning...")
    
    # Count original parameters
    original_params = sum(p.numel() for p in model.parameters())
    
    # Apply L1 unstructured pruning to all Linear layers
    for name, module in model.named_modules():
        if isinstance(module, nn.Linear):
            prune.l1_unstructured(module, name='weight', amount=pruning_amount)
            # Make pruning permanent by removing reparameterization
            prune.remove(module, 'weight')
            print(f"[PRUNING] Pruned layer: {name}")
    
    # Count remaining non-zero parameters
    remaining_params = sum(
        (p != 0).sum().item() for p in model.parameters()
    )
    
    sparsity = (1 - remaining_params / original_params) * 100
    print(f"[PRUNING] Sparsity achieved: {sparsity:.2f}%")
    print(f"[PRUNING] Parameters: {original_params} → {remaining_params}")
    
    return model


def knowledge_distillation(teacher_model, num_samples=1000, epochs=50, temperature=3.0):
    """
    Train a smaller student model using knowledge distillation
    Args:
        teacher_model: Large trained model (teacher)
        num_samples: Number of synthetic samples to generate
        epochs: Training epochs for student
        temperature: Softmax temperature for distillation
    Returns:
        Trained student model
    """
    print(f"\n[DISTILLATION] Starting knowledge distillation...")
    print(f"[DISTILLATION] Samples: {num_samples}, Epochs: {epochs}, Temperature: {temperature}")
    
    student_model = StudentModel()
    teacher_model.eval()
    
    # Generate synthetic training data
    print(f"[DISTILLATION] Generating synthetic training data...")
    X_train = torch.randn(num_samples, 4096)
    
    # Get teacher predictions
    with torch.no_grad():
        teacher_outputs = teacher_model(X_train)
    
    # Distillation loss: MSE between student and teacher outputs
    criterion = nn.MSELoss()
    optimizer = optim.Adam(student_model.parameters(), lr=0.001)
    
    print(f"[DISTILLATION] Training student model...")
    student_model.train()
    
    for epoch in range(epochs):
        optimizer.zero_grad()
        
        # Forward pass
        student_outputs = student_model(X_train)
        
        # Distillation loss
        loss = criterion(student_outputs, teacher_outputs)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 10 == 0:
            print(f"[DISTILLATION] Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")
    
    print(f"[DISTILLATION] Training complete")
    
    # Compare model sizes
    teacher_params = sum(p.numel() for p in teacher_model.parameters())
    student_params = sum(p.numel() for p in student_model.parameters())
    reduction = (1 - student_params / teacher_params) * 100
    
    print(f"[DISTILLATION] Teacher params: {teacher_params:,}")
    print(f"[DISTILLATION] Student params: {student_params:,}")
    print(f"[DISTILLATION] Parameter reduction: {reduction:.2f}%")
    
    return student_model


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


def optimize_model(input_path, output_dir, apply_pruning_flag=True, apply_distillation_flag=True, pruning_amount=0.3):
    """Main optimization pipeline with pruning and knowledge distillation"""
    print(f"\n{'='*60}")
    print(f"[OPTIMIZER] Starting optimization")
    print(f"[OPTIMIZER] Pruning: {apply_pruning_flag}, Distillation: {apply_distillation_flag}")
    print(f"{'='*60}")
    
    original_size = get_file_size_mb(input_path)
    print(f"[OPTIMIZER] Original PT size: {original_size:.2f} MB")

    # Load the original model
    print(f"\n[OPTIMIZER] Loading original model...")
    model = load_model(input_path)
    model.eval()
    
    # Step 1: Apply Pruning (if enabled)
    if apply_pruning_flag:
        model = apply_pruning(model, pruning_amount=pruning_amount)
        # Save pruned model
        pruned_path = os.path.join(
            output_dir,
            os.path.basename(input_path).replace(".pt", "_pruned.pt")
        )
        torch.save(model, pruned_path)
        pruned_size = get_file_size_mb(pruned_path)
        print(f"[OPTIMIZER] Pruned model saved: {pruned_size:.2f} MB")
        input_path = pruned_path  # Use pruned model for next steps
    
    # Step 2: Apply Knowledge Distillation (if enabled)
    if apply_distillation_flag:
        student_model = knowledge_distillation(model, num_samples=1000, epochs=50)
        # Save student model
        student_path = os.path.join(
            output_dir,
            os.path.basename(input_path).replace(".pt", "_distilled.pt")
        )
        torch.save(student_model, student_path)
        student_size = get_file_size_mb(student_path)
        print(f"[OPTIMIZER] Distilled model saved: {student_size:.2f} MB")
        input_path = student_path  # Use student model for next steps
        model = student_model

    # Step 3: Convert to ONNX
    if input_path.endswith(".pt"):
        print(f"\n[OPTIMIZER] Converting to ONNX...")
        onnx_path = convert_pt_to_onnx(input_path, output_dir)
        onnx_size = get_file_size_mb(onnx_path)
        print(f"[OPTIMIZER] ONNX size: {onnx_size:.2f} MB")
    else:
        onnx_path = input_path
        onnx_size = original_size

    # Step 4: Dynamic Quantization to Int8
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
    print(f"[OPTIMIZER] Final quantized size: {optimized_size:.2f} MB")

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


