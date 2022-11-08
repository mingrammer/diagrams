# This module is automatically generated by autogen.sh. DO NOT EDIT.

from . import _TencentCloud


class _Compute(_TencentCloud):
    _type = "compute"
    _icon_dir = "resources/tencentcloud/compute"


class AutoScaling(_Compute):
    _icon = "auto-scaling.png"


class BatchCompute(_Compute):
    _icon = "batch-compute.png"


class CloudPhysicalMachine(_Compute):
    _icon = "cloud-physical-machine.png"


class CloudVirtualMachine(_Compute):
    _icon = "cloud-virtual-machine.png"


class CvmDedicatedHost(_Compute):
    _icon = "cvm-dedicated-host.png"


class FpgaCloudComputing(_Compute):
    _icon = "fpga-cloud-computing.png"


class GpuCloudComputing(_Compute):
    _icon = "gpu-cloud-computing.png"


class Lighthouse(_Compute):
    _icon = "lighthouse.png"


# Aliases

CVM = CloudVirtualMachine
GPU = GpuCloudComputing
FPGA = FpgaCloudComputing
CPM = CloudPhysicalMachine
CDH = CvmDedicatedHost
AS = AutoScaling
Batch = BatchCompute
