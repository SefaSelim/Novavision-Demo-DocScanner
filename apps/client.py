"""
    Example requests for the DocScanner package: one per dependentDropdownlist
    option of each executor. These build the raw JSON payload the service's
    /api endpoint expects and can be sent with requests.post(...).

    Run a document photo through the pipeline like this:
        1. DocumentCrop (AutoCrop or PerspectiveCorrect) -> flattened page
        2. ScanEffect (BlackWhiteScan or ColorScan) on the cropped result
"""

import json
import base64

import requests

ENDPOINT_URL = "http://127.0.0.1:8000/api"


def _encode_image(path, mime_type="image/jpg"):
    with open(path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode("utf-8")
    return {
        "uID": "sample-1",
        "mimeType": mime_type,
        "encoding": "base64",
        "value": encoded,
    }


def _image_input(name, image_path):
    # PackageModel's InputImage.value is a single Image, not a list.
    return {
        "name": name,
        "value": _encode_image(image_path),
        "type": "object",
    }


def build_document_crop_auto_request(image_path="resources/sample_document.jpg"):
    return {
        "name": "DocScanner",
        "type": "component",
        "executor": {
            "name": "ConfigExecutor",
            "type": "executor",
            "field": "dependentDropdownlist",
            "value": {
                "name": "DocumentCrop",
                "type": "object",
                "field": "option",
                "value": {
                    "inputs": {
                        "inputImage": _image_input("inputImage", image_path),
                    },
                    "configs": {
                        "configCropType": {
                            "name": "configCropType",
                            "type": "object",
                            "field": "dependentDropdownlist",
                            "value": {
                                "name": "AutoCrop",
                                "value": "AutoCrop",
                                "type": "string",
                                "field": "option",
                                "paddingPx": {
                                    "name": "PaddingPx", "value": 10,
                                    "type": "number", "field": "textInput",
                                },
                                "edgeSensitivity": {
                                    "name": "EdgeSensitivity",
                                    "type": "object",
                                    "field": "dropdownlist",
                                    "value": {"name": "Low", "value": "Low", "type": "string", "field": "option"},
                                },
                            },
                        }
                    },
                },
            },
        },
    }


def build_document_crop_perspective_request(image_path="resources/sample_document.jpg"):
    return {
        "name": "DocScanner",
        "type": "component",
        "executor": {
            "name": "ConfigExecutor",
            "type": "executor",
            "field": "dependentDropdownlist",
            "value": {
                "name": "DocumentCrop",
                "type": "object",
                "field": "option",
                "value": {
                    "inputs": {
                        "inputImage": _image_input("inputImage", image_path),
                    },
                    "configs": {
                        "configCropType": {
                            "name": "configCropType",
                            "type": "object",
                            "field": "dependentDropdownlist",
                            "value": {
                                "name": "PerspectiveCorrect",
                                "value": "PerspectiveCorrect",
                                "type": "string",
                                "field": "option",
                                "cornerDetection": {
                                    "name": "CornerDetection",
                                    "type": "object",
                                    "field": "dropdownlist",
                                    "value": {"name": "Auto", "value": "Auto", "type": "string", "field": "option"},
                                },
                                "outputAspect": {
                                    "name": "OutputAspect", "value": 0.707,
                                    "type": "number", "field": "textInput",
                                },
                            },
                        }
                    },
                },
            },
        },
    }


def build_scan_effect_bw_request(image_path="resources/sample_cropped_document.jpg"):
    return {
        "name": "DocScanner",
        "type": "component",
        "executor": {
            "name": "ConfigExecutor",
            "type": "executor",
            "field": "dependentDropdownlist",
            "value": {
                "name": "ScanEffect",
                "type": "object",
                "field": "option",
                "value": {
                    "inputs": {
                        "inputImage": _image_input("inputImage", image_path),
                    },
                    "configs": {
                        "configScanType": {
                            "name": "configScanType",
                            "type": "object",
                            "field": "dependentDropdownlist",
                            "value": {
                                "name": "BlackWhiteScan",
                                "value": "BlackWhiteScan",
                                "type": "string",
                                "field": "option",
                                "sharpenLevel": {
                                    "name": "SharpenLevel", "value": 3,
                                    "type": "number", "field": "textInput",
                                },
                                "scanMode": {
                                    "name": "ScanMode",
                                    "type": "object",
                                    "field": "dropdownlist",
                                    "value": {
                                        "name": "HighContrastBW", "value": "HighContrastBW",
                                        "type": "string", "field": "option",
                                    },
                                },
                            },
                        }
                    },
                },
            },
        },
    }


def build_scan_effect_color_request(
    image_path="resources/sample_cropped_document.jpg",
    reference_path="resources/sample_reference_patch.jpg",
):
    return {
        "name": "DocScanner",
        "type": "component",
        "executor": {
            "name": "ConfigExecutor",
            "type": "executor",
            "field": "dependentDropdownlist",
            "value": {
                "name": "ScanEffect",
                "type": "object",
                "field": "option",
                "value": {
                    "inputs": {
                        "inputImage": _image_input("inputImage", image_path),
                        "inputReferenceImage": _image_input("inputReferenceImage", reference_path),
                    },
                    "configs": {
                        "configScanType": {
                            "name": "configScanType",
                            "type": "object",
                            "field": "dependentDropdownlist",
                            "value": {
                                "name": "ColorScan",
                                "value": "ColorScan",
                                "type": "string",
                                "field": "option",
                                "brightness": {
                                    "name": "Brightness", "value": 10,
                                    "type": "number", "field": "textInput",
                                },
                                "saturationBoost": {
                                    "name": "SaturationBoost", "value": 1.2,
                                    "type": "number", "field": "textInput",
                                },
                                "whiteBalance": {
                                    "name": "WhiteBalance",
                                    "type": "object",
                                    "field": "dropdownlist",
                                    "value": {
                                        "name": "Reference", "value": "Reference",
                                        "type": "string", "field": "option",
                                    },
                                },
                            },
                        }
                    },
                },
            },
        },
    }


def build_resize_fit_request(image_path="resources/sample_document.jpg"):
    return {
        "name": "DocScanner",
        "type": "component",
        "executor": {
            "name": "ConfigExecutor",
            "type": "executor",
            "field": "dependentDropdownlist",
            "value": {
                "name": "Resize",
                "type": "object",
                "field": "option",
                "value": {
                    "inputs": {
                        "inputImage": _image_input("inputImage", image_path),
                    },
                    "configs": {
                        "configResizeMode": {
                            "name": "configResizeMode",
                            "type": "object",
                            "field": "dependentDropdownlist",
                            "value": {
                                "name": "FitLongEdge",
                                "value": "FitLongEdge",
                                "type": "string",
                                "field": "option",
                                "maxEdge": {
                                    "name": "MaxEdge", "value": 1600,
                                    "type": "number", "field": "textInput",
                                },
                                "interpolation": {
                                    "name": "Interpolation",
                                    "type": "object",
                                    "field": "dropdownlist",
                                    "value": {"name": "Area", "value": "Area", "type": "string", "field": "option"},
                                },
                            },
                        }
                    },
                },
            },
        },
    }


def build_resize_exact_request(image_path="resources/sample_document.jpg"):
    return {
        "name": "DocScanner",
        "type": "component",
        "executor": {
            "name": "ConfigExecutor",
            "type": "executor",
            "field": "dependentDropdownlist",
            "value": {
                "name": "Resize",
                "type": "object",
                "field": "option",
                "value": {
                    "inputs": {
                        "inputImage": _image_input("inputImage", image_path),
                    },
                    "configs": {
                        "configResizeMode": {
                            "name": "configResizeMode",
                            "type": "object",
                            "field": "dependentDropdownlist",
                            "value": {
                                "name": "ExactSize",
                                "value": "ExactSize",
                                "type": "string",
                                "field": "option",
                                "targetWidth": {
                                    "name": "TargetWidth", "value": 1240,
                                    "type": "number", "field": "textInput",
                                },
                                "targetHeight": {
                                    "name": "TargetHeight", "value": 1754,
                                    "type": "number", "field": "textInput",
                                },
                                "fitMode": {
                                    "name": "FitMode",
                                    "type": "object",
                                    "field": "dropdownlist",
                                    "value": {"name": "Pad", "value": "Pad", "type": "string", "field": "option"},
                                },
                            },
                        }
                    },
                },
            },
        },
    }


def send(request_payload):
    response = requests.post(ENDPOINT_URL, json=request_payload)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    print(json.dumps(build_document_crop_auto_request(), indent=2))
    # send(build_document_crop_auto_request())
