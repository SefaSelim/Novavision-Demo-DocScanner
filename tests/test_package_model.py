"""
    Validates that PackageModel accepts a well-formed request payload for every
    dependentDropdownlist option of both executors. Runs inside the Image, where
    the real `sdks.novavision` package is importable.

        python -m pytest tests/test_package_model.py
"""

from components.DocScanner.src.models.PackageModel import PackageModel


def _image():
    return {"uID": "t", "mimeType": "image/jpg", "encoding": "base64", "value": "AA=="}


def _wrap(executor_name, executor_value):
    return {
        "name": "DocScanner",
        "type": "component",
        "configs": {
            "executor": {
                "name": "ConfigExecutor",
                "type": "executor",
                "field": "dependentDropdownlist",
                "value": {
                    "name": executor_name,
                    "type": "object",
                    "field": "option",
                    "value": executor_value,
                },
            }
        },
    }


def _crop(crop_type_value):
    return _wrap("DocumentCrop", {
        "inputs": {"inputImage": {"name": "inputImage", "value": _image(), "type": "object"}},
        "configs": {"configCropType": {
            "name": "configCropType", "type": "object",
            "field": "dependentDropdownlist", "value": crop_type_value,
        }},
    })


def _scan(scan_type_value, inputs):
    return _wrap("ScanEffect", {
        "inputs": inputs,
        "configs": {"configScanType": {
            "name": "configScanType", "type": "object",
            "field": "dependentDropdownlist", "value": scan_type_value,
        }},
    })


def _resize(resize_mode_value):
    return _wrap("Resize", {
        "inputs": {"inputImage": {"name": "inputImage", "value": _image(), "type": "object"}},
        "configs": {"configResizeMode": {
            "name": "configResizeMode", "type": "object",
            "field": "dependentDropdownlist", "value": resize_mode_value,
        }},
    })


def test_auto_crop():
    payload = _crop({
        "name": "AutoCrop", "value": "AutoCrop", "type": "string", "field": "option",
        "paddingPx": {"name": "PaddingPx", "value": 10, "type": "number", "field": "textInput"},
        "edgeSensitivity": {"name": "EdgeSensitivity", "type": "object", "field": "dropdownlist",
                            "value": {"name": "Low", "value": "Low", "type": "string", "field": "option"}},
    })
    model = PackageModel(**payload)
    assert model.configs.executor.value.name == "DocumentCrop"


def test_perspective_correct():
    payload = _crop({
        "name": "PerspectiveCorrect", "value": "PerspectiveCorrect", "type": "string", "field": "option",
        "cornerDetection": {"name": "CornerDetection", "type": "object", "field": "dropdownlist",
                            "value": {"name": "Auto", "value": "Auto", "type": "string", "field": "option"}},
        "outputAspect": {"name": "OutputAspect", "value": 0.707, "type": "number", "field": "textInput"},
    })
    model = PackageModel(**payload)
    assert model.configs.executor.value.name == "DocumentCrop"


def test_black_white_scan():
    inputs = {"inputImage": {"name": "inputImage", "value": _image(), "type": "object"}}
    payload = _scan({
        "name": "BlackWhiteScan", "value": "BlackWhiteScan", "type": "string", "field": "option",
        "sharpenLevel": {"name": "SharpenLevel", "value": 3, "type": "number", "field": "textInput"},
        "scanMode": {"name": "ScanMode", "type": "object", "field": "dropdownlist",
                    "value": {"name": "HighContrastBW", "value": "HighContrastBW", "type": "string", "field": "option"}},
    }, inputs)
    model = PackageModel(**payload)
    assert model.configs.executor.value.name == "ScanEffect"


def test_color_scan_with_reference():
    inputs = {
        "inputImage": {"name": "inputImage", "value": _image(), "type": "object"},
        "inputReferenceImage": {"name": "inputReferenceImage", "value": _image(), "type": "object"},
    }
    payload = _scan({
        "name": "ColorScan", "value": "ColorScan", "type": "string", "field": "option",
        "brightness": {"name": "Brightness", "value": 10, "type": "number", "field": "textInput"},
        "saturationBoost": {"name": "SaturationBoost", "value": 1.2, "type": "number", "field": "textInput"},
        "whiteBalance": {"name": "WhiteBalance", "type": "object", "field": "dropdownlist",
                        "value": {"name": "Reference", "value": "Reference", "type": "string", "field": "option"}},
    }, inputs)
    model = PackageModel(**payload)
    assert model.configs.executor.value.name == "ScanEffect"


def test_resize_fit_long_edge():
    payload = _resize({
        "name": "FitLongEdge", "value": "FitLongEdge", "type": "string", "field": "option",
        "maxEdge": {"name": "MaxEdge", "value": 1600, "type": "number", "field": "textInput"},
        "interpolation": {"name": "Interpolation", "type": "object", "field": "dropdownlist",
                         "value": {"name": "Area", "value": "Area", "type": "string", "field": "option"}},
    })
    model = PackageModel(**payload)
    assert model.configs.executor.value.name == "Resize"


def test_resize_exact_size():
    payload = _resize({
        "name": "ExactSize", "value": "ExactSize", "type": "string", "field": "option",
        "targetWidth": {"name": "TargetWidth", "value": 1240, "type": "number", "field": "textInput"},
        "targetHeight": {"name": "TargetHeight", "value": 1754, "type": "number", "field": "textInput"},
        "fitMode": {"name": "FitMode", "type": "object", "field": "dropdownlist",
                   "value": {"name": "Pad", "value": "Pad", "type": "string", "field": "option"}},
    })
    model = PackageModel(**payload)
    assert model.configs.executor.value.name == "Resize"
