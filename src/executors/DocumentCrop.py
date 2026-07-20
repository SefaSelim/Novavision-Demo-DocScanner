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
    def _quad_from_mask(mask, frame_area, candidates):
        # Takes the largest region in a binary mask and, if it is a plausible
        # page (big but not the entire frame), adds its 4 corners to candidates.
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        # Ignore near-frame regions (>97%): those are equivalent to "no crop",
        # so treating them as a detection would just hide a real smaller page.
        if not (0.20 * frame_area < area < 0.97 * frame_area):
            return
        perimeter = cv2.arcLength(largest, True)
        approx = cv2.approxPolyDP(largest, 0.02 * perimeter, True)
        if len(approx) == 4:
            candidates.append(approx.reshape(4, 2).astype("float32"))
        else:
            candidates.append(cv2.boxPoints(cv2.minAreaRect(largest)).astype("float32"))

    def _find_document_quad(self, image, edge_sensitivity="High"):
        # Finds the four corners of the WHOLE document using several strategies
        # and keeping the LARGEST plausible region, so a small inner element
        # (a table cell) is never mistaken for the page. If nothing large enough
        # is found the document most likely fills the frame, so we return None
        # and let the caller use the full image.
        height, width = image.shape[:2]
        frame_area = float(width * height)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        if edge_sensitivity == "Low":
            low_threshold, high_threshold = 20, 80
        else:
            low_threshold, high_threshold = 40, 130

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
        candidates = []

        # Strategy 1 - edges merged into one blob (captures a bordered form or a
        # table grid that reaches the page edges).
        edges = cv2.Canny(blurred, low_threshold, high_threshold)
        blob = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=3)
        blob = cv2.dilate(blob, kernel, iterations=1)
        self._quad_from_mask(blob, frame_area, candidates)

        # Strategy 2 - Otsu foreground/background segmentation, both polarities
        # (captures a page whose paper tone differs from its surroundings).
        _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        for mask in (otsu, cv2.bitwise_not(otsu)):
            closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            self._quad_from_mask(closed, frame_area, candidates)

        if not candidates:
            return None

        best = max(candidates, key=lambda q: cv2.contourArea(q.astype("float32")))
        # Only trust a detection that is plausibly the whole page. Otherwise the
        # document fills the frame - the caller should use the full image.
        if cv2.contourArea(best.astype("float32")) < 0.55 * frame_area:
            return None
        return best

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
        quad = self._find_document_quad(image, edge_sensitivity)

        if quad is None:
            # Could not find the document's 4 corners - return the whole frame
            # untouched rather than cropping to a wrong sub-region.
            print("[DocumentCrop] no document quad found - returning full frame")
            return image

        rect = self._order_points(quad)
        coverage = cv2.contourArea(rect.astype("float32")) / float(width * height)
        print(f"[DocumentCrop] AutoCrop document quad covers {coverage * 100:.1f}% of the frame")

        # 4-point crop: deskew the detected corners onto a straight rectangle,
        # keeping the document's own proportions (no aspect forcing here).
        result = self._warp_to_rect(image, rect, output_aspect=None)

        # paddingPx adds a uniform white margin around the cropped page.
        if padding_px and padding_px > 0:
            result = cv2.copyMakeBorder(
                result, padding_px, padding_px, padding_px, padding_px,
                cv2.BORDER_CONSTANT, value=(255, 255, 255)
            )
        return result

    def _perspective_correct(self, image, corner_detection, output_aspect):
        quad = None
        if corner_detection == "Auto":
            quad = self._find_document_quad(image, "High")

        if quad is None:
            # Fallback: Manual mode (no corners supplied) or Auto detection
            # failed - return the image untouched rather than raising.
            return image

        return self._warp_to_rect(image, self._order_points(quad), output_aspect=output_aspect)

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
