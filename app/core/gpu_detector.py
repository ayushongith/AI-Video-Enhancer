import logging
import subprocess
import re
from dataclasses import dataclass, field
from typing import Optional

import cv2

logger = logging.getLogger(__name__)


@dataclass
class GPUInfo:
    cuda_available: bool = False
    cuda_version: str = ""
    cuda_device_count: int = 0
    cuda_device_name: str = ""
    opencl_available: bool = False
    opencl_device_name: str = ""
    opencv_cuda_build: bool = False
    num_threads: int = 0


class GPUDetector:
    def __init__(self) -> None:
        self._info = GPUInfo()
        self._detect_all()

    def _detect_all(self) -> None:
        self._detect_opencv_cuda()
        self._detect_cuda_toolkit()
        self._detect_opencl()
        self._detect_threads()

    def _detect_opencv_cuda(self) -> None:
        try:
            build_info = cv2.getBuildInformation()
            if "CUDA" in build_info and "YES" in build_info.split("CUDA")[1][:5]:
                self._info.opencv_cuda_build = True
                cuda_match = re.search(r"CUDA_VERSION\s+(\S+)", build_info)
                if cuda_match:
                    self._info.cuda_version = cuda_match.group(1)
                try:
                    count = cv2.cuda.getCudaEnabledDeviceCount()
                    self._info.cuda_device_count = count
                    if count > 0:
                        cv2.cuda.setDevice(0)
                        self._info.cuda_device_name = cv2.cuda.getDevice().name()
                        self._info.cuda_available = True
                except Exception:
                    self._info.cuda_device_count = 0
        except Exception as e:
            logger.debug("OpenCV CUDA detection: %s", e)

    def _detect_cuda_toolkit(self) -> None:
        if self._info.cuda_available:
            return
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                self._info.cuda_device_name = result.stdout.strip().split(",")[0].strip()
                self._info.cuda_device_count = len(result.stdout.strip().split("\n"))
                self._info.cuda_available = True
                self._info.cuda_version = "toolkit"
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass

    def _detect_opencl(self) -> None:
        try:
            result = subprocess.run(
                ["clinfo", "--raw"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                self._info.opencl_available = True
                for line in result.stdout.split("\n"):
                    if "Device Name" in line and ":" in line:
                        name = line.split(":", 1)[-1].strip()
                        if name:
                            self._info.opencl_device_name = name
                            break
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            try:
                import pyopencl as cl
                platforms = cl.get_platforms()
                for plat in platforms:
                    devices = plat.get_devices()
                    if devices:
                        self._info.opencl_available = True
                        self._info.opencl_device_name = devices[0].name.strip()
                        break
            except ImportError:
                pass
            except Exception:
                pass

    def _detect_threads(self) -> None:
        import os
        self._info.num_threads = os.cpu_count() or 4

    @property
    def acceleration_label(self) -> str:
        if self._info.cuda_available and self._info.opencv_cuda_build:
            dev = self._info.cuda_device_name.split()[:1]
            name = ' '.join(dev) if dev else "GPU"
            return f"CUDA [{self._info.cuda_device_count}x {name}]"
        if self._info.cuda_available:
            dev = self._info.cuda_device_name.split()[:1]
            name = ' '.join(dev) if dev else "GPU"
            return f"GPU [{name}]"
        if self._info.opencl_available and self._info.opencl_device_name:
            dev = self._info.opencl_device_name.split()[:1]
            name = ' '.join(dev) if dev else "OpenCL"
            return f"OpenCL [{name}]"
        return f"CPU ({self._info.num_threads} threads)"

    @property
    def info(self) -> GPUInfo:
        return self._info

    def optimize_opencv(self, net: cv2.dnn.Net) -> None:
        if self._info.cuda_available and self._info.opencv_cuda_build:
            try:
                net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                logger.info("Optimized DNN for CUDA")
            except Exception:
                net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        else:
            net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
