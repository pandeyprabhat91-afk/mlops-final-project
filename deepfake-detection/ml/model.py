"""CNN+LSTM deepfake detector using EfficientNet-B0 as spatial feature extractor."""
import torch
import torch.nn as nn
from efficientnet_pytorch import EfficientNet


class DeepfakeDetector(nn.Module):
    """EfficientNet-B0 spatial encoder + 2-layer LSTM temporal classifier.

    Input:  (batch, num_frames, C, H, W)  — face-cropped frames
    Output: (batch, 1)                     — sigmoid probability (1=fake)
    """

    def __init__(
        self,
        num_frames: int = 30,
        lstm_hidden: int = 256,
        lstm_layers: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.num_frames = num_frames

        # Spatial feature extractor — pretrained ImageNet weights
        self.cnn = EfficientNet.from_pretrained("efficientnet-b0")
        cnn_out_features = self.cnn._fc.in_features
        self.cnn._fc = nn.Identity()  # remove classification head

        # Temporal classifier
        self.lstm = nn.LSTM(
            input_size=cnn_out_features,
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            batch_first=True,
            dropout=dropout,
        )
        self.classifier = nn.Sequential(
            nn.Linear(lstm_hidden, 128),  # Bottleneck layer before binary output
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )

    def forward_features(self, features: torch.Tensor) -> torch.Tensor:
        """Forward pass using pre-computed CNN features — skips EfficientNet entirely.

        Args:
            features: Tensor of shape (batch, num_frames, cnn_out_features)

        Returns:
            Tensor of shape (batch, 1) with sigmoid probabilities
        """
        lstm_out, _ = self.lstm(features)
        last_hidden = lstm_out[:, -1, :]
        return self.classifier(last_hidden)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Tensor of shape (batch, num_frames, C, H, W)

        Returns:
            Tensor of shape (batch, 1) with sigmoid probabilities
        """
        assert x.dim() == 5, f"Expected 5D input (batch, frames, C, H, W), got {x.dim()}D"
        assert x.shape[2:] == (3, 224, 224), f"Expected frames of shape (3, 224, 224), got {x.shape[2:]}"
        batch, frames, C, H, W = x.shape
        # Flatten batch+frames for CNN
        x = x.view(batch * frames, C, H, W)
        # Use no_grad for CNN when all its params are frozen — avoids storing
        # intermediate activations, cutting VRAM by ~60% and speeding up backward.
        cnn_frozen = not any(p.requires_grad for p in self.cnn.parameters())
        ctx = torch.no_grad() if cnn_frozen else torch.enable_grad()
        with ctx:
            features = self.cnn(x)  # (batch*frames, cnn_features)
        features = features.view(batch, frames, -1)  # (batch, frames, cnn_features)

        lstm_out, _ = self.lstm(features)  # (batch, frames, lstm_hidden)
        last_hidden = lstm_out[:, -1, :]  # take last timestep

        return self.classifier(last_hidden)
