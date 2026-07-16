"""
    Turns a cropped document photo into a "scanned" looking page, either a
    classic black & white paper look (BlackWhiteScan) or a colour-corrected
    photo scan (ColorScan). Also reports a simple quality score for the
    result so callers can flag low quality scans.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../'))

import cv2
import numpy as np

from sdks.novavision.src.media.image import Image
from sdks.novavision.src.base.component import Component
from sdks.novavision.src.helper.executor import Executor
from components.DocScanner.src.utils.response import build_scan_response
from components.DocScanner.src.utils.params import resolve_option_name
from components.DocScanner.src.models.PackageModel import PackageModel


class ScanEffect(Component):
    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)
        self.request.model = PackageModel(**(self.request.data))
        self.scan_type = resolve_option_name(self.request.get_param("configScanType"))
        self.sharpen_level = self.request.get_param("SharpenLevel")
        self.scan_mode = resolve_option_name(self.request.get_param("ScanMode"))
        self.brightness = self.request.get_param("Brightness")
        self.saturation_boost = self.request.get_param("SaturationBoost")
        self.white_balance = resolve_option_name(self.request.get_param("WhiteBalance"))
        self.image = self.request.get_param("inputImage")
        self.reference_image = self.request.get_param("inputReferenceImage")

    @staticmethod
    def bootstrap(config: dict = None) -> dict:
        # No model weights to load - ScanEffect is pure OpenCV. Report ready
        # so the registry / Bootstrap loop can confirm the executor is wired up.
        return {"status": "ready"}

    @staticmethod
    def _unsharp_mask(image, amount):
        if amount is None or amount <= 0:
            return image
        blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=2)
        weight = 1 + (amount / 10.0)
        return cv2.addWeighted(image, weight, blurred, 1 - weight, 0)

    def _black_white_scan(self, image, sharpen_level, scan_mode):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        if scan_mode == "GrayscaleSoft":
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            result = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        else:
            thresholded = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 25, 15
            )
            result = cv2.cvtColor(thresholded, cv2.COLOR_GRAY2BGR)

        return self._unsharp_mask(result, sharpen_level)

    @staticmethod
    def _gray_world_white_balance(image, reference_image=None):
        # Use the reference patch's channel averages if one was supplied,
        # otherwise fall back to the classic gray-world assumption on the
        # image itself.
        sample = reference_image if reference_image is not None else image
        result = image.astype("float32")
        avg_b, avg_g, avg_r = [sample[:, :, i].astype("float32").mean() for i in range(3)]
        avg_gray = (avg_b + avg_g + avg_r) / 3.0
        for i, avg_channel in enumerate([avg_b, avg_g, avg_r]):
            if avg_channel > 1e-3:
                result[:, :, i] *= (avg_gray / avg_channel)
        return np.clip(result, 0, 255).astype("uint8")

    def _color_scan(self, image, reference_image, brightness, saturation_boost, white_balance):
        # Only pull channel averages from the reference patch when the user
        # explicitly asked for it; otherwise fall back to plain gray-world.
        reference = reference_image if white_balance == "Reference" else None
        balanced = self._gray_world_white_balance(image, reference)

        hsv = cv2.cvtColor(balanced, cv2.COLOR_BGR2HSV).astype("float32")
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_boost, 0, 255)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] + brightness, 0, 255)
        return cv2.cvtColor(hsv.astype("uint8"), cv2.COLOR_HSV2BGR)

    @staticmethod
    def _quality_score(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        contrast = float(gray.std())
        score = min(100.0, (sharpness / 10.0) + contrast)
        return round(float(score), 2)

    def run(self):
        img = Image.get_frame(img=self.image, redis_db=self.redis_db)
        source = img.value

        reference_source = None
        if self.reference_image:
            reference_frame = Image.get_frame(img=self.reference_image, redis_db=self.redis_db)
            reference_source = reference_frame.value

        try:
            if self.scan_type == "BlackWhiteScan":
                result = self._black_white_scan(source, self.sharpen_level or 3, self.scan_mode or "HighContrastBW")
            else:
                result = self._color_scan(source, reference_source, self.brightness or 0, self.saturation_boost or 1.2, self.white_balance or "Auto")
        except Exception:
            # Never let a bad photo crash the executor - fall back to the
            # untouched source image.
            result = source

        quality_score = self._quality_score(result)

        img.value = result
        self.image = Image.set_frame(img=img, package_uID=self.uID, redis_db=self.redis_db)
        packageModel = build_scan_response(context=self, quality_score=quality_score)
        return packageModel


if "__main__" == __name__:
    Executor(sys.argv[1]).run()
