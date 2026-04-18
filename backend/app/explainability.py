"""Activation-map heatmap generation for model explainability."""
import base64
import io
import logging
from typing import Optional

import numpy as np
import torch
from PIL import Image

logger = logging.getLogger(__name__)


def generate_gradcam(
    model: torch.nn.Module,
    frames_tensor: torch.Tensor,
    target_layer_name: str = "cnn._blocks",
) -> Optional[str]:
    """Generate an activation heatmap for the middle frame.

    Uses activation CAM (no backward pass) — captures the last EfficientNet
    block's feature map, averages across channels, and overlays on the frame.
    Much faster than Grad-CAM: no gradient computation required.

    Args:
        model: DeepfakeDetector model
        frames_tensor: Tensor of shape (num_frames, 3, 224, 224) — NOT batched

    Returns:
        Base64-encoded PNG of heatmap overlay, or empty string on failure.
    """
    try:
        model.eval()

        mid_idx = len(frames_tensor) // 2
        single_frame = frames_tensor[mid_idx].unsqueeze(0)  # (1, 3, 224, 224)

        activations = []

        def forward_hook(module, input, output):
            activations.append(output.detach())

        target_layer = None
        if hasattr(model.cnn, "_blocks") and len(model.cnn._blocks) > 0:
            target_layer = model.cnn._blocks[-1]

        if target_layer is None:
            logger.warning("gradcam_target_layer_not_found")
            return ""

        handle = target_layer.register_forward_hook(forward_hook)
        try:
            with torch.no_grad():
                model.cnn(single_frame)
        finally:
            handle.remove()

        if not activations:
            return ""

        # Average across channels → (H, W) heatmap
        act = activations[0][0]  # (C, H, W)
        heatmap = act.mean(dim=0).cpu().numpy()
        heatmap = np.maximum(heatmap, 0)
        heatmap_max = heatmap.max()
        if heatmap_max > 0:
            heatmap = heatmap / heatmap_max

        # Overlay on middle frame
        mid_frame = frames_tensor[mid_idx]
        frame_np = mid_frame.permute(1, 2, 0).cpu().numpy()
        frame_np = (frame_np * 255).clip(0, 255).astype(np.uint8)

        heatmap_uint8 = (heatmap * 255).astype(np.uint8)
        heatmap_resized = np.array(Image.fromarray(heatmap_uint8).resize((224, 224)))

        overlay = frame_np.copy()
        overlay[:, :, 0] = np.clip(
            overlay[:, :, 0].astype(int) + heatmap_resized.astype(int) // 2,
            0, 255,
        ).astype(np.uint8)

        pil_img = Image.fromarray(overlay)
        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    except Exception as e:
        logger.error("gradcam_failed", extra={"error": str(e)})
        return ""
