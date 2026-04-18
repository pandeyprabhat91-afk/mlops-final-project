# tests/unit/test_validate_schema.py
import torch
import pytest
from pathlib import Path


def test_validate_valid_tensor(tmp_path):
    from ml.validate_schema import validate_feature_file

    pt_path = tmp_path / "video_real.pt"
    tensor = torch.zeros(30, 3, 224, 224)
    torch.save(tensor, str(pt_path))
    errors = validate_feature_file(str(pt_path))
    assert errors == []


def test_validate_wrong_shape(tmp_path):
    from ml.validate_schema import validate_feature_file

    pt_path = tmp_path / "bad_real.pt"
    tensor = torch.zeros(5, 3, 64, 64)  # wrong spatial dims
    torch.save(tensor, str(pt_path))
    errors = validate_feature_file(str(pt_path))
    assert any("224" in e for e in errors)


def test_validate_missing_label(tmp_path):
    from ml.validate_schema import validate_feature_file

    pt_path = tmp_path / "videounlabeled.pt"
    tensor = torch.zeros(30, 3, 224, 224)
    torch.save(tensor, str(pt_path))
    errors = validate_feature_file(str(pt_path))
    assert any("label" in e.lower() for e in errors)
