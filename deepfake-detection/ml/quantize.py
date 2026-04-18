"""Post-training dynamic quantization for on-prem deployment.

Dynamic quantization converts Linear and LSTM weights to INT8 at runtime
without a calibration dataset — ideal for CPU-only environments.
"""
import sys
from pathlib import Path

import torch
import torch.quantization

sys.path.insert(0, str(Path(__file__).parent.parent))


def quantize_model(model: torch.nn.Module, output_path: str) -> None:
    """Apply dynamic INT8 quantization to Linear and LSTM layers.

    Args:
        model: Trained DeepfakeDetector in eval mode
        output_path: Path to write the quantized model (.pt)
    """
    model.eval()
    quantized = torch.quantization.quantize_dynamic(
        model,
        {torch.nn.Linear, torch.nn.LSTM},
        dtype=torch.qint8,
    )
    torch.save(quantized, output_path)
    original_mb = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024 * 1024)
    print(f"Quantized model saved to {output_path}")
    print(f"Original parameter size: {original_mb:.1f} MB (weights quantized to INT8)")


if __name__ == "__main__":
    import argparse
    import mlflow.pytorch

    parser = argparse.ArgumentParser(description="Quantize deepfake model")
    parser.add_argument("--run_id", type=str, required=True, help="MLflow run ID")
    parser.add_argument("--output", type=str, default="ml/best_model_quantized.pt")
    args = parser.parse_args()

    device = torch.device("cpu")  # quantization targets CPU
    model = mlflow.pytorch.load_model(f"runs:/{args.run_id}/model")
    model = model.to(device)
    quantize_model(model, args.output)
    print(f"Quantized model written to {args.output}")
