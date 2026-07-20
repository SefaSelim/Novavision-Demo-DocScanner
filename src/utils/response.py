
from sdks.novavision.src.helper.package import PackageHelper
from components.DocScanner.src.models.PackageModel import (
    PackageModel, PackageConfigs, ConfigExecutor,
    DocumentCropOutputs, DocumentCropResponse, DocumentCropExecutor, OutputImage,
    ScanEffectOutputs, ScanEffectResponse, ScanEffectExecutor, OutputQualityScore,
    ResizeOutputs, ResizeResponse, ResizeExecutor,
)


def build_crop_response(context):
    outputImage = OutputImage(value=context.image)
    outputs = DocumentCropOutputs(outputImage=outputImage)
    response = DocumentCropResponse(outputs=outputs)
    executor = DocumentCropExecutor(value=response)
    configExecutor = ConfigExecutor(value=executor)
    packageConfigs = PackageConfigs(executor=configExecutor)
    package = PackageHelper(packageModel=PackageModel, packageConfigs=packageConfigs)
    packageModel = package.build_model(context)
    return packageModel


def build_scan_response(context, quality_score):
    outputImage = OutputImage(value=context.image)
    outputQualityScore = OutputQualityScore(value=quality_score)
    outputs = ScanEffectOutputs(outputImage=outputImage, outputQualityScore=outputQualityScore)
    response = ScanEffectResponse(outputs=outputs)
    executor = ScanEffectExecutor(value=response)
    configExecutor = ConfigExecutor(value=executor)
    packageConfigs = PackageConfigs(executor=configExecutor)
    package = PackageHelper(packageModel=PackageModel, packageConfigs=packageConfigs)
    packageModel = package.build_model(context)
    return packageModel


def build_resize_response(context):
    outputImage = OutputImage(value=context.image)
    outputs = ResizeOutputs(outputImage=outputImage)
    response = ResizeResponse(outputs=outputs)
    executor = ResizeExecutor(value=response)
    configExecutor = ConfigExecutor(value=executor)
    packageConfigs = PackageConfigs(executor=configExecutor)
    package = PackageHelper(packageModel=PackageModel, packageConfigs=packageConfigs)
    packageModel = package.build_model(context)
    return packageModel
