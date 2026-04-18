"""Grad-CAM heatmap generation for model explainability."""
import base64
import io
import logging
from typing import Optional

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

logger = logging.getLogger(__name__)


def generate_gradcam(
    model: torch.nn.Module,
    frames_tensor: torch.Tensor,
    target_layer_name: str = "cnn._blocks",
) -> Optional[str]:
    """Generate Grad-CAM heatmap for the most influential frame.

    Hooks the last EfficientNet block to capture activations and gradients,
    then overlays a heatmap onto the middle frame of the sequence.

    Args:
        model: DeepfakeDetector model (must be in eval mode with grad enabled)
        frames_tensor: Tensor of shape (num_frames, 3, 224, 224) — NOT batched
        target_layer_name: Name prefix of the CNN layer to hook

    Returns:
        Base64-encoded PNG of Grad-CAM overlay on the middle frame,
        or empty string on failure (never raises).
    """
    try:
        model.eval()
        input_tensor = frames_tensor.unsqueeze(0)  # (1, F, 3, 224, 224)

        gradients = []
        activations = []

        def forward_hook(module, input, output):
            activations.append(output)

        def backward_hook(module, grad_in, grad_out):
            gradients.append(grad_out[0])

        # Hook the last EfficientNet MBConvBlock directly
        target_layer = None
        if hasattr(model.cnn, "_blocks") and len(model.cnn._blocks) > 0:
            target_layer = model.cnn._blocks[-1]

        if target_layer is None:
            logger.warning("gradcam_target_layer_not_found")
            return ""

        fwd_handle = target_layer.register_forward_hook(forward_hook)
        bwd_handle = target_layer.register_backward_hook(backward_hook)

        try:
            output = model(input_tensor)
            model.zero_grad()
            output.backward()
        finally:
            fwd_handle.remove()
            bwd_handle.remove()

        if not gradients or not activations:
            return ""

        # Pool gradients across spatial dimensions and weight activations
        pooled_gradients = gradients[0].mean(dim=[0, 2, 3])
        activation = activations[0][0].clone()
        for i in range(activation.shape[0]):
            activation[i, :, :] *= pooled_gradients[i]

        heatmap = activation.mean(dim=0).detach().cpu().numpy()
        heatmap = np.maximum(heatmap, 0)
        heatmap_max = heatmap.max()
        if heatmap_max > 0:
            heatmap = heatmap / heatmap_max

        # Overlay heatmap on the middle frame (denormalized)
        mid_idx = len(frames_tensor) // 2
        mid_frame = frames_tensor[mid_idx]
        frame_np = mid_frame.permute(1, 2, 0).detach().cpu().numpy()
        # Denormalize from ImageNet stats
        frame_np = frame_np * np.array([0.229, 0.224, 0.225]) + np.array([0.485, 0.456, 0.406])
        frame_np = (frame_np * 255).clip(0, 255).astype(np.uint8)

        heatmap_uint8 = (heatmap * 255).astype(np.uint8)
        heatmap_resized = np.array(
            Image.fromarray(heatmap_uint8).resize((224, 224))
        )

        # Red channel overlay
        overlay = frame_np.copy()
        overlay[:, :, 0] = np.clip(
            overlay[:, :, 0].astype(int) + heatmap_resized.astype(int) // 2,
            0, 255
        ).astype(np.uint8)

        # Encode to base64 PNG
        pil_img = Image.fromarray(overlay)
        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    except Exception as e:
        logger.error("gradcam_failed", extra={"error": str(e)})
        return ""
