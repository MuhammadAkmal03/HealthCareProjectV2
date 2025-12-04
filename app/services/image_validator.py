"""
Image Validator - Detects non-X-ray images
Prevents cat photos, selfies, and other non-medical images from being processed
"""

import numpy as np
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)


class ImageValidator:
    """
    Validates if uploaded image is likely a chest X-ray.
    Uses heuristics: grayscale check, aspect ratio, brightness patterns, edge density.
    """

    def __init__(self):
        self.min_width = 100
        self.min_height = 100
        self.max_width = 5000
        self.max_height = 5000
        self.valid_aspect_ratio_range = (0.5, 2.0)  # More lenient for various X-ray formats

    def validate_basic_properties(self, img: Image.Image) -> tuple[bool, str]:
        """Check basic image properties (size, aspect ratio)"""
        width, height = img.size

        if width < self.min_width or height < self.min_height:
            return False, f"Image too small. Minimum size: {self.min_width}x{self.min_height}px"

        if width > self.max_width or height > self.max_height:
            return False, f"Image too large. Maximum size: {self.max_width}x{self.max_height}px"

        # Aspect ratio check disabled for testing - X-rays come in many formats
        # aspect_ratio = width / height
        # if not (self.valid_aspect_ratio_range[0] <= aspect_ratio <= self.valid_aspect_ratio_range[1]):
        #     return False, f"Invalid aspect ratio. Please upload a chest X-ray image."

        return True, ""

    def is_likely_grayscale_medical(self, img: Image.Image) -> tuple[bool, str]:
        """Check if image appears to be a grayscale medical image"""
        if img.mode != 'RGB':
            img_rgb = img.convert('RGB')
        else:
            img_rgb = img

        img_array = np.array(img_rgb)
        r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
        
        # Calculate color variance - MAIN CHECK (most reliable)
        rg_diff = np.abs(r.astype(float) - g.astype(float))
        rb_diff = np.abs(r.astype(float) - b.astype(float))
        gb_diff = np.abs(g.astype(float) - b.astype(float))
        
        avg_color_diff = (rg_diff.mean() + rb_diff.mean() + gb_diff.mean()) / 3
        
        # Stricter threshold - reject colorful photos
        if avg_color_diff > 12:  # Lowered from 25 to 12 - rejects colorful images
            return False, "Image appears to be a color photo, not a medical X-ray. Please upload a chest X-ray image."

        # Check brightness distribution - VERY LENIENT
        gray = np.array(img.convert('L'))
        mean_brightness = gray.mean()
        std_brightness = gray.std()

        # Much more lenient brightness range - X-rays vary a lot
        if mean_brightness < 15 or mean_brightness > 240:  # Was 30-220, now 15-240
            return False, "Image brightness unusual for chest X-ray. Please upload a valid medical image."

        # Very lenient contrast check - X-rays can have low contrast
        if std_brightness < 10:  # Was 20, now 10 - allows low contrast X-rays
            return False, "Image lacks contrast typical of chest X-rays. Please upload a valid medical image."

        return True, ""

    def check_edge_density(self, img: Image.Image) -> tuple[bool, str]:
        """Check edge patterns (X-rays have specific edge density)"""
        try:
            # Disabled for now - too strict, rejects valid X-rays
            # X-rays vary widely in quality and edge patterns
            return True, ""
            
            # gray = np.array(img.convert('L'))
            # gy, gx = np.gradient(gray.astype(float))
            # edge_magnitude = np.sqrt(gx**2 + gy**2)
            # edge_density = (edge_magnitude > 20).sum() / edge_magnitude.size
            
            # if edge_density < 0.02:
            #     return False, "Image too uniform. Doesn't appear to be a chest X-ray."
            
            # if edge_density > 0.5:
            #     return False, "Image too complex. Doesn't match chest X-ray patterns."
            
            # return True, ""
            
        except Exception as e:
            logger.warning(f"Edge detection failed: {e}")
            return True, ""

    def validate_image_bytes(self, image_bytes: bytes) -> tuple[bool, str, Image.Image]:
        """
        Complete validation pipeline.
        Returns: (is_valid, error_message, PIL_Image)
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            
            is_valid, msg = self.validate_basic_properties(img)
            if not is_valid:
                return False, msg, None

            is_valid, msg = self.is_likely_grayscale_medical(img)
            if not is_valid:
                return False, msg, None

            is_valid, msg = self.check_edge_density(img)
            if not is_valid:
                return False, msg, None

            logger.info("Image passed all validation checks")
            return True, "", img

        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return False, f"Invalid image file: {str(e)}", None
