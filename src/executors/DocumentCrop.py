"""
    Detects a document in a photo and crops/flattens it, either by a simple
    padded bounding-box crop (AutoCrop) or by a full perspective correction
    onto a flat rectangle (PerspectiveCorrect).
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../'))

import cv2
import numpy as np

from sdks.novavision.src.media.image import Image
from sdks.novavision.src.base.component import Component
from sdks.novavision.src.helper.executor import Executor
from components.DocScanner.src.utils.response import build_crop_response
from components.DocScanner.src.utils.params import resolve_option_name
from components.DocScanner.src.models.PackageModel import PackageModel


class DocumentCrop(Component):
    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)
        self.request.model = PackageModel(**(self.request.data))
        self.crop_type = resolve_option_name(self.request.get_param("configCropType"))
        self.padding_px = self.request.get_param("PaddingPx")
        self.edge_sensitivity = resolve_option_name(self.request.get_param("EdgeSensitivity"))
        self.corner_detection = resolve_option_name(self.request.get_param("CornerDetection"))
        self.output_aspect = self.request.get_param("OutputAspect")
        self.image = self.request.get_param("inputImage")

    @staticmethod
    def bootstrap(config: dict = None) -> dict:
        # No model weights to load - DocumentCrop is pure OpenCV. Report ready
        # so the registry / Bootstrap loop can confirm the executor is wired up.
        return {"status": "ready"}

    @staticmethod
    def _to_uint8(image):
        # Incoming frames may arrive as float (0-1 or 0-255); Canny and the
        # other OpenCV ops below assume an 8-bit image, so normalise up front.
        if image is None or image.dtype == np.uint8:
            return image
        image = image.astype("float32")
        if image.max() <= 1.0:
            image = image * 255.0
        return np.clip(image, 0, 255).astype("uint8")

    @staticmethod
    def _order_points(pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    @staticmethod
    def _find_document_contour(image, edge_sensitivity):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        if edge_sensitivity == "Low":
            low_threshold, high_threshold = 30, 100
        else:
            low_threshold, high_threshold = 75, 200

        edges = cv2.Canny(blurred, low_threshold, high_threshold)
        edges = cv2.dilate(edges, None, iterations=1)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            if len(approx) == 4:
                return approx.reshape(4, 2).astype("float32")

        return None

    @staticmethod
    def _warp_to_rect(image, rect, output_aspect=None):
        # Deskews the four ordered corners onto a flat rectangle. When
        # output_aspect is None the document's own measured proportions are
        # kept; otherwise width/height is forced to the given aspect.
        (tl, tr, br, bl) = rect
        width_top = np.linalg.norm(tr - tl)
        width_bottom = np.linalg.norm(br - bl)
        height_left = np.linalg.norm(bl - tl)
        height_right = np.linalg.norm(br - tr)

        max_width = max(int(max(width_top, width_bottom)), 1)
        if output_aspect:
            # outputAspect is width/height (0.707 ~= A4 portrait)
            max_height = max(int(max_width / output_aspect), 1)
        else:
            max_height = max(int(max(height_left, height_right)), 1)

        destination = np.array([
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1]
        ], dtype="float32")

        matrix = cv2.getPerspectiveTransform(rect, destination)
        return cv2.warpPerspective(image, matrix, (max_width, max_height))

    def _auto_crop(self, image, padding_px, edge_sensitivity):
        height, width = image.shape[:2]
        contour = self._find_document_contour(image, edge_sensitivity)

        if contour is None:
            # Fallback: no clear document contour found, just shave the
            # requested padding off every side instead of failing.
            x1 = min(padding_px, max(width // 2 - 1, 0))
            y1 = min(padding_px, max(height // 2 - 1, 0))
            return image[y1:height - y1, x1:width - x1]

        # Deskew onto the document's own proportions so a rotated/tilted page
        # comes out straight (a plain bounding box would keep the skew), then
        # add a uniform padding border so nothing is clipped at the edges.
        warped = self._warp_to_rect(image, self._order_points(contour), output_aspect=None)
        if padding_px and padding_px > 0:
            warped = cv2.copyMakeBorder(
                warped, padding_px, padding_px, padding_px, padding_px,
                cv2.BORDER_CONSTANT, value=(255, 255, 255)
            )
        return warped

    def _perspective_correct(self, image, corner_detection, output_aspect):
        contour = None
        if corner_detection == "Auto":
            contour = self._find_document_contour(image, "High")

        if contour is None:
            # Fallback: Manual mode (no corners supplied) or Auto detection
            # failed - return the image untouched rather than raising.
            return image

        return self._warp_to_rect(image, self._order_points(contour), output_aspect=output_aspect)

    def run(self):
        img = Image.get_frame(img=self.image, redis_db=self.redis_db)
        source = self._to_uint8(img.value)

        try:
            if self.crop_type == "AutoCrop":
                result = self._auto_crop(source, self.padding_px or 10, self.edge_sensitivity or "High")
            else:
                result = self._perspective_correct(source, self.corner_detection or "Auto", self.output_aspect or 0.707)
        except Exception:
            # Never let a bad photo crash the executor - return the source
            # image untouched as the safest possible fallback.
            result = source

        img.value = result
        self.image = Image.set_frame(img=img, package_uID=self.uID, redis_db=self.redis_db)
        packageModel = build_crop_response(context=self)
        return packageModel


if "__main__" == __name__:
    Executor(sys.argv[1]).run()
