import subprocess
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from mayavi import mlab
from tqdm import tqdm

from latviz import utils


# TODO: write issue on problem of value outside vmin/vmax.
# TODO: add better messages
# TODO: fix avi and mp4 options to properly center the camera.


# Future ideas:
# - allow for user specified camera and scene settings(.json or .yaml?)


def create_animation(
    frame_folder: Path,
    animation_folder: Path,
    observable: str,
    time_slice: int,
    method: str,
    animation_type: str,
    frame_rate: Optional[int] = 10,
    verbose: Optional[bool] = False,
):
    """
    Method for created gifs and movies from generated 3D figures.

    Args:
        frame_folder: folder path to figures that will be be stiched together.
        animation_folder: folder path to place animations in.
        observable: observable we are creating a gif or a movie for.
        time_slice: eucl or flow time slice.
        method: type of 3D plot.
        animation_type: format of animation. Avaliable: 'gif', 'avi'
        figsize: integer tuple of the figure size.
    Raises:
        AssertionError: if animation_type is not recognized.
    """

    # Removes spaces
    observable = observable.replace(" ", "_")

    input_paths = frame_folder / "frame_t%02d.png"

    animation_path = animation_folder / (
        f"{observable.lower()}_{method}_{time_slice}d.{animation_type}"
    )

    if animation_type == "gif":
        # TODO: add note of this in README.md
        cmd = [
            "convert",
            "-delay",
            "1",
            "-loop",
            "0",
            str(frame_folder / "*.png"),
            str(animation_path),
        ]

    elif animation_type == "mp4":
        cmd = [
            "ffmpeg",
            "-r",
            str(frame_rate),
            "-start_number",
            "0",
            "-i",
            str(input_paths),
            "-c:v",
            "libx264",
            "-crf",
            "0",
            "-preset",
            "veryslow",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "320k",
            "-y",
            str(animation_path),
        ]

    elif animation_type == "avi":
        cmd = [
            "ffmpeg",
            "-r",
            str(frame_rate),
            "-i",
            str(input_paths),
            "-y",
            "-qscale:v",
            "0",
            str(animation_path),
        ]
    else:
        raise NameError(
            f"{animation_type} is not a recognized animation type."
        )

    if verbose:
        print(f"> {' '.join(cmd)}")

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    _ = proc.stdout.read()

    print(f"Animation {animation_path} created.")


def plot_iso_surface(
    field: np.ndarray,
    observable_name: str,
    frame_folder: Path,
    file_type: str = "png",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    n_contours: int = 30,
    camera_distance: float = 0.65,
    xlabel: str = "x",
    ylabel: str = "y",
    zlabel: str = "z",
    title: Optional["str"] = None,
    figsize: Tuple[int, int] = (1280, 1280),
    correction_factor: Optional[float] = None,
    verbose: bool = False,
) -> None:
    """
    Function for plotting iso surfaces and animate the result.

    Args:
        field: field array of size (N,N,N,NT) to plot. The number of
            points to animate over is always the last dimension.
        observable_name: str of observable_name we are plotting.
        frame_folder: location of where to temporary store frames.
        file_type: string of file extension type. Default is 'png'.
        vmin: float lower cutoff value of the field. Default is None.
        vmax: float upper cutoff value of the field. Default is None.
        n_contours: optional integer argument for number of contours.
            Default is 15.
        correction_factor: optional, default None. Will correct plot values
            with correction_factor.
        verbose: default is False
    """

    assert isinstance(
        observable_name, str
    ), "Observable name must be string type"
    utils.check_folder(frame_folder, dryrun=False, verbose=verbose)

    NT, N = field.shape[:2]

    if correction_factor is not None:
        assert isinstance(correction_factor, float), (
            f"Correction factor is not of type float: {correction_factor} "
            f"type: {type(correction_factor)}"
        )

        field *= correction_factor

    if title is not None:
        title += ", "
    else:
        title = ""

    if vmin is None:
        vmin = np.min(field)

    if vmax is None:
        vmax = np.max(field)

    # Sets up the contours
    contour_list = np.linspace(vmin, vmax, n_contours)
    contour_list = contour_list.tolist()

    # Makes sure we do not show figure
    mlab.options.offscreen = True

    f = mlab.figure(size=figsize, bgcolor=(0.9, 0.9, 0.9), fgcolor=(0, 0, 0))

    # Render options
    f.scene.render_window.point_smoothing = True
    f.scene.render_window.line_smoothing = True
    f.scene.render_window.polygon_smoothing = True
    f.scene.render_window.multi_samples = 8  # Try with 4 if this is slow

    for it in tqdm(range(NT), desc=f"Rendering {observable_name}"):
        mlab.clf(figure=f)

        # print (np.min(field[it]), np.max(field[it]))

        source = mlab.pipeline.scalar_field(field[it], figure=f)
        mlab.pipeline.iso_surface(
            source,
            vmin=vmin,
            vmax=vmax,
            contours=contour_list,
            reset_zoom=False,
            opacity=0.5,
            figure=f,
        )

        # Adjusts camera view
        mlab.view(
            45,
            70,
            distance=np.sqrt(N ** 3) * camera_distance,
            focalpoint=(N / 2.0, N / 2.0, N / 2.0),
            figure=f,
        )

        # mlab.draw(f)

        mlab.scalarbar(title="Contour", orientation="vertical")
        mlab.title(title + f"t={it:02d}", size=0.4, height=0.94)

        # Sets ticks on axis
        _ = mlab.axes(figure=f, nb_labels=5)

        mlab.xlabel(xlabel)
        mlab.ylabel(ylabel)
        mlab.zlabel(zlabel)

        # Creates outline of box
        mlab.outline()

        fpath = frame_folder / f"frame_t{it:02d}.{file_type}"

        mlab.savefig(str(fpath), figure=f, magnification="auto", size=None)

        if verbose:
            tqdm.write(f"file created at {fpath}")

    mlab.close()
