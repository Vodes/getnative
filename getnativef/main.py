import argparse
from pathlib import Path
from .process import process, get_plot
from .utils import to_float
from .kernels import get_kernel_from_args, common_kernels
from .log import info, debug, warn

from vskernels import Bicubic, Bilinear, Kernel
from vstools import vs, core
from vssource import source

parser = argparse.ArgumentParser(description="Find the native resolution(s) of upscaled material (mostly anime)")


def kernel_args():
    parser.add_argument(
        "--kernel",
        "-k",
        dest="kernel",
        type=str.lower,
        default="catrom",
        help="Resize kernel to be used. Can be any common kernel from vskernels.",
    )
    parser.add_argument(
        "--bicubic-b",
        "-b",
        dest="b",
        type=to_float,
        default="1/3",
        help="B parameter of bicubic resize",
    )
    parser.add_argument(
        "--bicubic-c",
        "-c",
        dest="c",
        type=to_float,
        default="1/3",
        help="C parameter of bicubic resize",
    )
    parser.add_argument(
        "--taps",
        "-t",
        dest="taps",
        type=int,
        default=3,
        help="Taps parameter of lanczos resize",
    )


def size_args():
    parser.add_argument(
        "--min-height",
        "-min",
        dest="min_h",
        type=int,
        default=700,
        help="Minimum height to consider",
    )
    parser.add_argument(
        "--max-height",
        "-max",
        dest="max_h",
        type=int,
        default=1000,
        help="Maximum height to consider",
    )
    parser.add_argument(
        "--stepping",
        "-steps",
        dest="steps",
        type=float,
        default=None,
        help="Example steps=3 [500p, 503p, 506p ...]",
    )
    parser.add_argument(
        "--direction",
        "-d",
        dest="direction",
        type=str.lower,
        default="h",
        help="Direction to test in. Width/Height",
    )
    parser.add_argument(
        "--base-height",
        "-bh",
        dest="base_height",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--base-width",
        "-bw",
        dest="base_width",
        type=int,
        default=None,
    )


def output_args():
    parser.add_argument(
        "--plot-format",
        "-pf",
        dest="plot_format",
        type=str.lower,
        default="png",
        help="Format of the output image. Specify multiple formats separated by commas. Can be svg, png, pdf, rgba, jp(e)g, tif(f), and probably more",
    )
    parser.add_argument(
        "--show-plot-gui",
        "-pg",
        dest="show_plot",
        action="store_true",
        default=True,
        help="Show an interactive plot gui window.",
    )
    parser.add_argument(
        "--no-save",
        "-ns",
        dest="no_save",
        action="store_true",
        default=False,
        help="Do not save files to disk. Disables all output arguments!",
    )
    parser.add_argument(
        "--output-dir",
        "-dir",
        dest="dir",
        type=str,
        default="",
        help="Sets the path of the output dir where you want all results to be saved. (/results will always be added as last folder)",
    )


parser.add_argument(
    "--frame",
    "-f",
    dest="frame",
    type=int,
    default=0,
    help="Specify a frame for the analysis. 0 if unspecified.",
)

kernel_args()
size_args()
output_args()

parser.add_argument(
    dest="input_file",
    type=str,
    help="Absolute or relative path to the input file",
)
parser.add_argument(
    "--mode",
    "-m",
    dest="mode",
    type=str,
    choices=["bilinear", "bicubic", "bl-bc", "all"],
    default=None,
    help='Choose a predefined mode ["bilinear", "bicubic", "bl-bc", "all"]',
)


def main():
    debug("Called via 'getnative'. Assuming integer res and steps = 1")
    _main(False)


def fmain():
    debug("Called via 'getfnative'. Assuming float res and steps = 0.05")
    _main(True)


def _main(frac: bool):
    args = parser.parse_args()
    match args.mode:
        case "bilinear":
            kernels = [Bilinear()]
        case "bicubic":
            kernels = [kernel for kernel in common_kernels if isinstance(kernel, Bicubic)]
        case "bl-bc":
            kernels = [kernel for kernel in common_kernels if isinstance(kernel, Bicubic)]
            kernels.append(Bilinear())
        case "all":
            kernels = common_kernels
        case _:
            kernels = [get_kernel_from_args(args.kernel, args.b, args.c, args.taps)]

    if not args.steps:
        args.steps = 0.05 if frac else 1

    if not float(args.steps).is_integer() and not args.base_height:
        warn("You're attempting to check for fractional resolution without passing a base-height!\nAssuming max-height as base-height.")
        args.base_height = args.max_h

    if Path(args.input_file).suffix.lower() in {".py", ".pyw", ".vpy"}:
        import runpy

        runpy.run_path(str(Path(args.input_file).resolve()), {}, "__vapoursynth__")
        node = vs.get_output(0)

        if not isinstance(node, vs.VideoNode):
            try:
                node = node[0]
            except:
                raise ValueError("Please set a proper output node in the script you want to pass.")
    else:
        clip = source(args.input_file)

    try:
        clip = clip[int(args.frame)]
    except:
        raise ValueError(f"Could not get frame {args.frame} from indexed file!")

    for kernel in kernels:
        get_plot(process(clip, kernel, args.min_h, args.max_h, args.steps, args.direction, args.base_height, args.base_width), kernel, args)
