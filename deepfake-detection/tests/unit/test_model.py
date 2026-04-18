import pytest
import torch
from ml.model import DeepfakeDetector


@pytest.fixture
def model():
    m = DeepfakeDetector()
    m.eval()
    return m


def test_output_shape(model):
    x = torch.randn(2, 30, 3, 224, 224)
    with torch.no_grad():
        out = model(x)
    assert out.shape == (2, 1), f"Expected (2,1), got {out.shape}"


def test_output_in_range(model):
    x = torch.randn(1, 30, 3, 224, 224)
    with torch.no_grad():
        out = model(x)
    assert 0.0 <= out.item() <= 1.0


def test_different_batch_sizes(model):
    """Model must work for batch sizes 1, 4."""
    for batch in [1, 4]:
        x = torch.randn(batch, 30, 3, 224, 224)
        with torch.no_grad():
            out = model(x)
        assert out.shape == (batch, 1)


def test_model_has_parameters(model):
    """Model must have trainable parameters."""
    params = list(model.parameters())
    assert len(params) > 0
    total = sum(p.numel() for p in params)
    assert total > 1_000_000  # EfficientNet-B0 alone is ~5M params


def test_gradient_flows(model):
    """Gradients must flow from output back to classifier parameters."""
    model.train()
    x = torch.randn(1, 30, 3, 224, 224)
    out = model(x)
    loss = out.sum()
    loss.backward()
    # Check at least one classifier parameter has gradients
    classifier_grad = model.classifier[0].weight.grad
    assert classifier_grad is not None
    assert classifier_grad.abs().sum() > 0


def test_deterministic_with_eval(model):
    """model.eval() must produce consistent outputs (no dropout noise)."""
    x = torch.randn(1, 30, 3, 224, 224)
    with torch.no_grad():
        out1 = model(x)
        out2 = model(x)
    assert torch.allclose(out1, out2), "Model outputs differ in eval mode"
