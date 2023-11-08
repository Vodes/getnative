import vskernels
from vskernels import Catrom, Mitchell, Hermite, Lanczos, BicubicSharp, Bilinear, Kernel, KernelT, Bicubic, ComplexKernel

from inspect import isclass
from types import ModuleType

common_kernels = [
    # Bicubic
    Catrom(),
    Mitchell(),
    Hermite(),
    BicubicSharp(),
    # Lanczos
    Lanczos(2),
    Lanczos(3),
    Lanczos(4),
    # Other
    Bilinear(),
]

if hasattr(vskernels.kernels.bicubic, "FFmpegBicubic"):
    common_kernels.extend([vskernels.FFmpegBicubic(), vskernels.AdobeBicubic()])


# Stolen from getfscaler
def get_kernel_name(kernel: KernelT) -> tuple[str, str]:
    kernel = Kernel.ensure_obj(kernel)

    kernel_name = kernel.__class__.__name__
    extended_name = kernel_name

    if isinstance(kernel, Bicubic):
        extended_name += f" (Bicubic b={kernel.b:.2f}, c={kernel.c:.2f})"
    elif isinstance(kernel, Lanczos):
        extended_name += f" (taps={kernel.taps})"

    return kernel_name, extended_name


def get_kernels(module: ModuleType) -> list[KernelT]:
    classes = {getattr(module, attr) for attr in dir(module) if isclass(getattr(module, attr))}
    blacklist = ["Bicubic", "BicubicAuto", "ComplexKernel", "SetsuCubic", "ZewiaCubic"]
    return list({cl for cl in classes if issubclass(cl, ComplexKernel) and hasattr(cl, "descale") and cl.__name__ not in blacklist})


def get_kernel_from_args(name: str, b: float, c: float, taps: int) -> Kernel:
    if name.lower() == "bicubic":
        return Bicubic(b, c)
    elif name.lower() == "lanczos":
        return Lanczos(taps)
    elif name.lower() == "bilinear":
        return Bilinear()
    else:
        kernels = get_kernels(vskernels.kernels.bicubic)
        kernels.extend(get_kernels(vskernels.kernels.spline))

        for kernel in kernels:
            if kernel.__name__.lower() == name.lower():
                return Kernel.ensure_obj(kernel)

        raise ValueError("Could not find kernel for given name!")
