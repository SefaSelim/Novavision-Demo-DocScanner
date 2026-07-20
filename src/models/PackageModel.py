
from pydantic import Field
from typing import Optional, Union, Literal
from sdks.novavision.src.base.model import Package, Image, Inputs, Configs, Outputs, Response, Request, Output, Input, Config


# ---------------------------------------------------------------------------
# Shared Input / Output
# ---------------------------------------------------------------------------

class InputImage(Input):
    name: Literal["inputImage"] = "inputImage"
    value: Image
    type: Literal["object"] = "object"

    class Config:
        title = "Image"


class OutputImage(Output):
    name: Literal["outputImage"] = "outputImage"
    value: Image
    type: Literal["object"] = "object"

    class Config:
        title = "Image"


# ---------------------------------------------------------------------------
# Executor 1 - DocumentCrop : 1 input / 1 output
# ---------------------------------------------------------------------------

class PaddingPx(Config):
    """
        Margin kept around the detected document edge after cropping.
    """
    name: Literal["PaddingPx"] = "PaddingPx"
    value: int = Field(ge=0, le=50, default=10)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"
    placeHolder: Literal["[0, 50]"] = "[0, 50]"

    class Config:
        title = "Padding (px)"


class EdgeSensitivityLow(Config):
    name: Literal["Low"] = "Low"
    value: Literal["Low"] = "Low"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"

    class Config:
        title = "Low"


class EdgeSensitivityHigh(Config):
    name: Literal["High"] = "High"
    value: Literal["High"] = "High"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"

    class Config:
        title = "High"


class EdgeSensitivity(Config):
    """
        Low catches more, noisier edges; High keeps only strong edges.
    """
    name: Literal["EdgeSensitivity"] = "EdgeSensitivity"
    value: Union[EdgeSensitivityLow, EdgeSensitivityHigh]
    type: Literal["object"] = "object"
    field: Literal["dropdownlist"] = "dropdownlist"

    class Config:
        title = "Edge Sensitivity"


class AutoCrop(Config):
    """
        Crops around the detected document contour with a fixed padding.
    """
    name: Literal["AutoCrop"] = "AutoCrop"
    value: Literal["AutoCrop"] = "AutoCrop"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"
    paddingPx: PaddingPx
    edgeSensitivity: EdgeSensitivity

    class Config:
        title = "Auto Crop"


class CornerDetectionAuto(Config):
    name: Literal["Auto"] = "Auto"
    value: Literal["Auto"] = "Auto"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"

    class Config:
        title = "Auto"


class CornerDetectionManual(Config):
    name: Literal["Manual"] = "Manual"
    value: Literal["Manual"] = "Manual"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"

    class Config:
        title = "Manual"


class CornerDetection(Config):
    """
        Auto: 4 corners are found from the largest quadrilateral contour.
        Manual: no corner input is taken, the full image is used as a fallback.
    """
    name: Literal["CornerDetection"] = "CornerDetection"
    value: Union[CornerDetectionAuto, CornerDetectionManual]
    type: Literal["object"] = "object"
    field: Literal["dropdownlist"] = "dropdownlist"

    class Config:
        title = "Corner Detection"


class OutputAspect(Config):
    """
        Target width/height ratio of the corrected output, e.g. 0.707 for A4.
    """
    name: Literal["OutputAspect"] = "OutputAspect"
    value: float = Field(ge=0.5, le=2.0, default=0.707)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"
    placeHolder: Literal["[0.5, 2.0]"] = "[0.5, 2.0]"

    class Config:
        title = "Output Aspect Ratio"


class PerspectiveCorrect(Config):
    """
        Warps the document onto a flat rectangle using its 4 detected corners.
    """
    name: Literal["PerspectiveCorrect"] = "PerspectiveCorrect"
    value: Literal["PerspectiveCorrect"] = "PerspectiveCorrect"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"
    cornerDetection: CornerDetection
    outputAspect: OutputAspect

    class Config:
        title = "Perspective Correct"


class ConfigCropType(Config):
    name: Literal["configCropType"] = "configCropType"
    value: Union[AutoCrop, PerspectiveCorrect]
    type: Literal["object"] = "object"
    field: Literal["dependentDropdownlist"] = "dependentDropdownlist"

    class Config:
        title = "Crop Type"


class DocumentCropInputs(Inputs):
    inputImage: InputImage


class DocumentCropConfigs(Configs):
    configCropType: ConfigCropType


class DocumentCropOutputs(Outputs):
    outputImage: OutputImage


class DocumentCropRequest(Request):
    inputs: Optional[DocumentCropInputs]
    configs: DocumentCropConfigs

    class Config:
        json_schema_extra = {
            "target": "configs"
        }


class DocumentCropResponse(Response):
    outputs: DocumentCropOutputs


class DocumentCropExecutor(Config):
    name: Literal["DocumentCrop"] = "DocumentCrop"
    value: Union[DocumentCropRequest, DocumentCropResponse]
    type: Literal["object"] = "object"
    field: Literal["option"] = "option"

    class Config:
        title = "Document Crop"
        json_schema_extra = {
            "target": {
                "value": 0
            }
        }


# ---------------------------------------------------------------------------
# Executor 2 - ScanEffect : 2 inputs / 2 outputs
# ---------------------------------------------------------------------------

class InputReferenceImage(Input):
    """
        Optional second photo (e.g. a blank patch shot under the same light)
        used as a white-balance / contrast reference for ColorScan.
    """
    name: Literal["inputReferenceImage"] = "inputReferenceImage"
    value: Image
    type: Literal["object"] = "object"

    class Config:
        title = "Reference Image"


class OutputQualityScore(Output):
    """
        Simple sharpness/contrast metric (0-100) computed on the scanned output.
    """
    name: Literal["outputQualityScore"] = "outputQualityScore"
    value: float
    type: Literal["number"] = "number"

    class Config:
        title = "Quality Score"


class SharpenLevel(Config):
    name: Literal["SharpenLevel"] = "SharpenLevel"
    value: int = Field(ge=0, le=10, default=3)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"
    placeHolder: Literal["[0, 10]"] = "[0, 10]"

    class Config:
        title = "Sharpen Level"


class ScanModeHighContrastBW(Config):
    name: Literal["HighContrastBW"] = "HighContrastBW"
    value: Literal["HighContrastBW"] = "HighContrastBW"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"

    class Config:
        title = "High Contrast B/W"


class ScanModeGrayscaleSoft(Config):
    name: Literal["GrayscaleSoft"] = "GrayscaleSoft"
    value: Literal["GrayscaleSoft"] = "GrayscaleSoft"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"

    class Config:
        title = "Grayscale Soft"


class ScanMode(Config):
    """
        HighContrastBW: adaptive threshold, crisp black/white paper look.
        GrayscaleSoft: CLAHE-enhanced grayscale, keeps tonal detail.
    """
    name: Literal["ScanMode"] = "ScanMode"
    value: Union[ScanModeHighContrastBW, ScanModeGrayscaleSoft]
    type: Literal["object"] = "object"
    field: Literal["dropdownlist"] = "dropdownlist"

    class Config:
        title = "Mode"


class BlackWhiteScan(Config):
    """
        Classic scanned-document look, best for text pages.
    """
    name: Literal["BlackWhiteScan"] = "BlackWhiteScan"
    value: Literal["BlackWhiteScan"] = "BlackWhiteScan"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"
    sharpenLevel: SharpenLevel
    scanMode: ScanMode

    class Config:
        title = "Black & White Scan"


class Brightness(Config):
    name: Literal["Brightness"] = "Brightness"
    value: float = Field(ge=-50, le=50, default=10)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"
    placeHolder: Literal["[-50, 50]"] = "[-50, 50]"

    class Config:
        title = "Brightness"


class SaturationBoost(Config):
    name: Literal["SaturationBoost"] = "SaturationBoost"
    value: float = Field(ge=0.5, le=2.0, default=1.2)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"
    placeHolder: Literal["[0.5, 2.0]"] = "[0.5, 2.0]"

    class Config:
        title = "Saturation Boost"


class WhiteBalanceAuto(Config):
    name: Literal["Auto"] = "Auto"
    value: Literal["Auto"] = "Auto"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"

    class Config:
        title = "Auto (Gray World)"


class WhiteBalanceReference(Config):
    name: Literal["Reference"] = "Reference"
    value: Literal["Reference"] = "Reference"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"

    class Config:
        title = "From Reference Image"


class WhiteBalance(Config):
    """
        Auto: gray-world assumption on the image itself.
        Reference: use inputReferenceImage's channel averages.
    """
    name: Literal["WhiteBalance"] = "WhiteBalance"
    value: Union[WhiteBalanceAuto, WhiteBalanceReference]
    type: Literal["object"] = "object"
    field: Literal["dropdownlist"] = "dropdownlist"

    class Config:
        title = "White Balance"


class ColorScan(Config):
    """
        Keeps colour, corrects white balance and lifts brightness/saturation.
    """
    name: Literal["ColorScan"] = "ColorScan"
    value: Literal["ColorScan"] = "ColorScan"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"
    brightness: Brightness
    saturationBoost: SaturationBoost
    whiteBalance: WhiteBalance

    class Config:
        title = "Color Scan"


class ConfigScanType(Config):
    name: Literal["configScanType"] = "configScanType"
    value: Union[BlackWhiteScan, ColorScan]
    type: Literal["object"] = "object"
    field: Literal["dependentDropdownlist"] = "dependentDropdownlist"

    class Config:
        title = "Scan Type"


class ScanEffectInputs(Inputs):
    inputImage: InputImage
    inputReferenceImage: Optional[InputReferenceImage] = None


class ScanEffectConfigs(Configs):
    configScanType: ConfigScanType


class ScanEffectOutputs(Outputs):
    outputImage: OutputImage
    outputQualityScore: OutputQualityScore


class ScanEffectRequest(Request):
    inputs: Optional[ScanEffectInputs]
    configs: ScanEffectConfigs

    class Config:
        json_schema_extra = {
            "target": "configs"
        }


class ScanEffectResponse(Response):
    outputs: ScanEffectOutputs


class ScanEffectExecutor(Config):
    name: Literal["ScanEffect"] = "ScanEffect"
    value: Union[ScanEffectRequest, ScanEffectResponse]
    type: Literal["object"] = "object"
    field: Literal["option"] = "option"

    class Config:
        title = "Scan Effect"
        json_schema_extra = {
            "target": {
                "value": 0
            }
        }


# ---------------------------------------------------------------------------
# Executor 3 - Resize : 1 input / 1 output
# ---------------------------------------------------------------------------

# --- FitLongEdge option ---
class MaxEdge(Config):
    name: Literal["MaxEdge"] = "MaxEdge"
    value: int = Field(ge=64, le=8000, default=1600)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"
    placeHolder: Literal["[64, 8000]"] = "[64, 8000]"

    class Config:
        title = "Max Edge (px)"


class InterpolationArea(Config):
    name: Literal["Area"] = "Area"
    value: Literal["Area"] = "Area"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"

    class Config:
        title = "Area (best for shrinking)"


class InterpolationCubic(Config):
    name: Literal["Cubic"] = "Cubic"
    value: Literal["Cubic"] = "Cubic"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"

    class Config:
        title = "Cubic (best for enlarging)"


class Interpolation(Config):
    name: Literal["Interpolation"] = "Interpolation"
    value: Union[InterpolationArea, InterpolationCubic]
    type: Literal["object"] = "object"
    field: Literal["dropdownlist"] = "dropdownlist"

    class Config:
        title = "Interpolation"


class FitLongEdge(Config):
    """
        Scales the image so its longest edge equals maxEdge, keeping aspect.
    """
    name: Literal["FitLongEdge"] = "FitLongEdge"
    value: Literal["FitLongEdge"] = "FitLongEdge"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"
    maxEdge: MaxEdge
    interpolation: Interpolation

    class Config:
        title = "Fit Long Edge"


# --- ExactSize option ---
class TargetWidth(Config):
    name: Literal["TargetWidth"] = "TargetWidth"
    value: int = Field(ge=16, le=8000, default=1240)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"
    placeHolder: Literal["[16, 8000]"] = "[16, 8000]"

    class Config:
        title = "Target Width (px)"


class TargetHeight(Config):
    name: Literal["TargetHeight"] = "TargetHeight"
    value: int = Field(ge=16, le=8000, default=1754)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"
    placeHolder: Literal["[16, 8000]"] = "[16, 8000]"

    class Config:
        title = "Target Height (px)"


class FitStretch(Config):
    name: Literal["Stretch"] = "Stretch"
    value: Literal["Stretch"] = "Stretch"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"

    class Config:
        title = "Stretch to fit"


class FitPad(Config):
    name: Literal["Pad"] = "Pad"
    value: Literal["Pad"] = "Pad"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"

    class Config:
        title = "Keep aspect + pad"


class FitMode(Config):
    name: Literal["FitMode"] = "FitMode"
    value: Union[FitStretch, FitPad]
    type: Literal["object"] = "object"
    field: Literal["dropdownlist"] = "dropdownlist"

    class Config:
        title = "Fit Mode"


class ExactSize(Config):
    """
        Resizes to an exact width x height, either stretched or aspect-padded.
    """
    name: Literal["ExactSize"] = "ExactSize"
    value: Literal["ExactSize"] = "ExactSize"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"
    targetWidth: TargetWidth
    targetHeight: TargetHeight
    fitMode: FitMode

    class Config:
        title = "Exact Size"


class ConfigResizeMode(Config):
    name: Literal["configResizeMode"] = "configResizeMode"
    value: Union[FitLongEdge, ExactSize]
    type: Literal["object"] = "object"
    field: Literal["dependentDropdownlist"] = "dependentDropdownlist"

    class Config:
        title = "Resize Mode"


class ResizeInputs(Inputs):
    inputImage: InputImage


class ResizeConfigs(Configs):
    configResizeMode: ConfigResizeMode


class ResizeOutputs(Outputs):
    outputImage: OutputImage


class ResizeRequest(Request):
    inputs: Optional[ResizeInputs]
    configs: ResizeConfigs

    class Config:
        json_schema_extra = {
            "target": "configs"
        }


class ResizeResponse(Response):
    outputs: ResizeOutputs


class ResizeExecutor(Config):
    name: Literal["Resize"] = "Resize"
    value: Union[ResizeRequest, ResizeResponse]
    type: Literal["object"] = "object"
    field: Literal["option"] = "option"

    class Config:
        title = "Resize"
        json_schema_extra = {
            "target": {
                "value": 0
            }
        }


# ---------------------------------------------------------------------------
# Package level
# ---------------------------------------------------------------------------

class ConfigExecutor(Config):
    name: Literal["ConfigExecutor"] = "ConfigExecutor"
    value: Union[DocumentCropExecutor, ScanEffectExecutor, ResizeExecutor]
    type: Literal["executor"] = "executor"
    field: Literal["dependentDropdownlist"] = "dependentDropdownlist"

    class Config:
        title = "Task"


class PackageConfigs(Configs):
    executor: ConfigExecutor


class PackageModel(Package):
    configs: PackageConfigs
    type: Literal["component"] = "component"
    name: Literal["DocScanner"] = "DocScanner"
