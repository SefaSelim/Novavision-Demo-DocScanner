"""
    Resizes the incoming image on demand. Two modes:
      - FitLongEdge : scale so the longest edge equals maxEdge (keeps aspect).
      - ExactSize   : resize to an exact width x height, either stretched or
                      aspect-preserving with white padding.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../'))

import cv2
import numpy as np

from sdks.novavision.src.media.image import Image
from sdks.novavision.src.base.component import Component
from sdks.novavision.src.helper.executor import Executor
from components.DocScanner.src.utils.response import build_resize_response
from components.DocScanner.src.utils.params import resolve_option_name
from components.DocScanner.src.models.PackageModel import PackageModel


class Resize(Component):
    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)
        self.request.model = PackageModel(**(self.request.data))
        self.resize_mode = resolve_option_name(self.request.get_param("configResizeMode"))
        self.max_edge = self.request.get_param("MaxEdge")
        self.interpolation = resolve_option_name(self.request.get_param("Interpolation"))
        self.target_width = self.request.get_param("TargetWidth")
        self.target_height = self.request.get_param("TargetHeight")
        self.fit_mode = resolve_option_name(self.request.get_param("FitMode"))
        self.image = self.request.get_param("inputImage")

    @staticmethod
    def bootstrap(config: dict = None) -> dict:
        # No model weights to load - Resize is pure OpenCV. Report ready
        # so the registry / Bootstrap loop can confirm the executor is wired up.
        return {"status": "ready"}

    @staticmethod
    def _to_uint8(image):
        # Incoming frames may arrive as float (0-1 or 0-255); normalise to 8-bit.
        if image is None or image.dtype == np.uint8:
            return image
        image = image.astype("float32")
        if image.max() <= 1.0:
            image = image * 255.0
        return np.clip(image, 0, 255).astype("uint8")

    @staticmethod
    def _interp_flag(name, scale):
        if name == "Cubic":
            return cv2.INTER_CUBIC
        if name == "Area":
            return cv2.INTER_AREA
        # Sensible default: AREA when shrinking, CUBIC when enlarging.
        return cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC

    def _fit_long_edge(self, image, max_edge, interpolation):
        height, width = image.shape[:2]
        longest = max(height, width)
        if longest == 0:
            return image
        scale = float(max_edge) / float(longest)
        new_size = (max(int(round(width * scale)), 1), max(int(round(height * scale)), 1))
        return cv2.resize(image, new_size, interpolation=self._interp_flag(interpolation, scale))

    @staticmethod
    def _blank_like(image, height, width):
        # White canvas that matches the image's channel count.
        if image.ndim == 2:
            return np.full((height, width), 255, dtype="uint8")
        return np.full((height, width, image.shape[2]), 255, dtype="uint8")

    def _exact_size(self, image, target_width, target_height, fit_mode):
        target_width = max(int(target_width), 1)
        target_height = max(int(target_height), 1)

        if fit_mode == "Stretch":
            # Ignore aspect ratio and fill the box exactly.
            return cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)

        # Pad: keep aspect, fit inside the box, centre it on a white canvas.
        height, width = image.shape[:2]
        scale = min(target_width / float(width), target_height / float(height))
        new_w = max(int(round(width * scale)), 1)
        new_h = max(int(round(height * scale)), 1)
        interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
        resized = cv2.resize(image, (new_w, new_h), interpolation=interp)

        canvas = self._blank_like(image, target_height, target_width)
        x = (target_width - new_w) // 2
        y = (target_height - new_h) // 2
        canvas[y:y + new_h, x:x + new_w] = resized
        return canvas

    def run(self):
        img = Image.get_frame(img=self.image, redis_db=self.redis_db)
        source = self._to_uint8(img.value)

        in_h, in_w = source.shape[:2]
        try:
            if self.resize_mode == "ExactSize":
                result = self._exact_size(
                    source, self.target_width or 1240, self.target_height or 1754,
                    self.fit_mode or "Pad"
                )
            else:
                result = self._fit_long_edge(source, self.max_edge or 1600, self.interpolation or "Area")
        except Exception:
            # Never let a bad photo crash the executor - return the source
            # image untouched as the safest possible fallback.
            result = source

        out_h, out_w = result.shape[:2]
        in_aspect = round(in_w / float(in_h), 3) if in_h else 0
        out_aspect = round(out_w / float(out_h), 3) if out_h else 0
        print(
            f"[Resize] {self.resize_mode or 'FitLongEdge'}: "
            f"{in_w}x{in_h} (aspect {in_aspect}) -> {out_w}x{out_h} (aspect {out_aspect})"
        )

        img.value = result
        self.image = Image.set_frame(img=img, package_uID=self.uID, redis_db=self.redis_db)
        packageModel = build_resize_response(context=self)
        return packageModel


if "__main__" == __name__:
    Executor(sys.argv[1]).run()
