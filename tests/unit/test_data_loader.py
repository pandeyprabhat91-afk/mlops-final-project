import torch
import pytest
from ml.data_loader import FrameDataset, get_dataloaders

def test_dataset_getitem():
    frames = torch.randn(30, 3, 224, 224)
    samples = [(frames, 1), (frames, 0)]
    ds = FrameDataset(samples)
    x, y = ds[0]
    assert x.shape == (30, 3, 224, 224)
    assert y in (0, 1)

def test_dataset_len():
    samples = [(torch.randn(30, 3, 224, 224), 0)] * 5
    ds = FrameDataset(samples)
    assert len(ds) == 5

def test_get_dataloaders_split():
    samples = [(torch.randn(30, 3, 224, 224), i % 2) for i in range(10)]
    train_loader, val_loader = get_dataloaders(samples, batch_size=2, val_split=0.2)
    assert len(train_loader.dataset) == 8
    assert len(val_loader.dataset) == 2
