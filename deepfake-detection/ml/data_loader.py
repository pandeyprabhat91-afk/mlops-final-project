"""Frame dataset and dataloader utilities."""
from typing import List, Optional, Tuple

import torch
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms

TRAIN_TRANSFORM = transforms.Compose([
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

EVAL_TRANSFORM = transforms.Compose([
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class FrameDataset(Dataset):
    """Dataset of (frame_tensor, label) tuples.

    Args:
        samples: List of (tensor[num_frames, C, H, W], int_label) tuples
        transform: Optional per-frame transform applied to each frame
    """

    def __init__(
        self,
        samples: List[Tuple[torch.Tensor, int]],
        transform: Optional[transforms.Compose] = None,
    ):
        self.samples = samples
        self.transform = transform

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        frames, label = self.samples[idx]
        if self.transform:
            frames = torch.stack([self.transform(f) for f in frames])
        return frames, label


def get_dataloaders(
    samples: List[Tuple[torch.Tensor, int]],
    batch_size: int = 8,
    val_split: float = 0.2,
    num_workers: int = 0,
    transform: Optional[transforms.Compose] = "default",
) -> Tuple[DataLoader, DataLoader]:
    """Split samples into train/val and return DataLoaders.

    Args:
        samples: List of (tensor, label) tuples
        batch_size: Batch size for both loaders
        val_split: Fraction of data for validation
        num_workers: DataLoader worker processes (0 = main process, safe on Windows)

    Returns:
        (train_loader, val_loader)
    """
    val_size = int(len(samples) * val_split)
    train_size = len(samples) - val_size
    train_samples, val_samples = random_split(samples, [train_size, val_size])

    # "default" uses image augmentation transforms; None skips all transforms
    # (used when samples are pre-extracted CNN features, not raw image tensors)
    train_tx = TRAIN_TRANSFORM if transform == "default" else transform
    val_tx = EVAL_TRANSFORM if transform == "default" else transform
    train_ds = FrameDataset(list(train_samples), transform=train_tx)
    val_ds = FrameDataset(list(val_samples), transform=val_tx)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    return train_loader, val_loader
