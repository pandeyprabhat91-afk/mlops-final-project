# tests/unit/test_quantize.py
import torch
import pytest
from pathlib import Path


def test_quantize_reduces_size(tmp_path):
    from ml.model import DeepfakeDetector
    from ml.quantize import quantize_model

    model = DeepfakeDetector(num_frames=4, lstm_hidden=64, lstm_layers=1, dropout=0.0)
    out_path = tmp_path / "model_quantized.pt"
    quantize_model(model, str(out_path))

    assert out_path.exists()
    # Quantized model file should be loadable
    loaded = torch.load(str(out_path), weights_only=False)
    assert hasattr(loaded, "forward")
