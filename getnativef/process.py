from vstools import vs, core, get_y, depth, Colorspace, get_w, Matrix
from vsscale import fdescale_args
from vskernels import Kernel

from .kernels import get_kernel_name
from .log import info

import gc
from numpy import arange
from argparse import Namespace
import matplotlib.pyplot as plot
from matplotlib.figure import figaspect
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, TimeElapsedColumn


def process(
    clip: vs.VideoNode, kernel: Kernel, min_h: int, max_h: int, steps: float, direction: str, base_height: int | None, base_width: int | None
) -> tuple[list[float], list[float]]:
    start = float(min_h)
    end = float(max_h)
    step = float(steps)
    decimals = str(step)[::-1].find(".")
    if decimals < 0:
        decimals = 0
    attempts = [round(val, decimals) for val in arange(start, end + step, step) if round(val, decimals) <= end]

    clip = Colorspace.YUV(clip, matrix_in=Matrix.from_video(clip), matrix=Matrix.BT709)
    clip = depth(get_y(clip), 32)

    if step.is_integer():
        clips = [kernel.scale(kernel.descale(clip, get_w(height, clip, mod=None), height), clip.width, clip.height) for height in attempts]
    else:
        clips = list[vs.VideoNode]()
        for height in attempts:
            dscale, rscale = fdescale_args(clip, height, base_height, base_width, mode=direction, up_rate=1.0)
            descaled = kernel.descale(clip, **dscale)
            rescaled = kernel.scale(descaled, clip.width, clip.height, **rscale)
            clips.append(rescaled)

    full_clip = core.std.Splice(clips, mismatch=False)
    # expr_full = core.std.Expr([clip * full_clip.num_frames, full_clip], "x y - abs dup 0.015 > swap 0 ?")
    expr_full = core.std.Expr([clip * full_clip.num_frames, full_clip], "x y - 2 pow")
    full_clip = core.std.CropRel(expr_full, 10, 10, 10, 10).std.PlaneStats()

    errors = [0.0] * len(attempts)

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        TimeElapsedColumn(),
        TextColumn("{task.completed}/{task.total}"),
    ) as pro:
        task = pro.add_task(f"Checking {get_kernel_name(kernel)[1]}", total=full_clip.num_frames)

        for n, f in enumerate(full_clip.frames(close=True)):
            pro.update(task, completed=n + 1)
            errors[n] = f.props["PlaneStatsAverage"]

        pro.stop()

    gc.collect()

    best = attempts[errors.index(min(errors))]
    info(f"Lowest error found at a height of {best}")
    return (attempts, errors)


def get_plot(data: tuple[list[float], list[float]], kernel: Kernel, args: Namespace):
    from numpy import arange

    p = plot.figure()
    plot.close("all")
    plot.style.use("dark_background")
    _, ax = plot.subplots(figsize=figaspect(1 / 2))

    ax.plot(data[0], data[1], ".w-", linewidth=1)
    ax.set(xlabel="Height", ylabel="Error", yscale="log")
    ax.set_title(get_kernel_name(kernel)[1])

    # if not args.no_save:
    #     debug("saving not implemented yet")

    if args.show_plot:
        plot.show()

    plot.close(p)
