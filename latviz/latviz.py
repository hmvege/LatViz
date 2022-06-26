import subprocess
from pathlib import Path
from typing import Optional

import numpy as np
import pyvista as pv
from loguru import logger
from tqdm import tqdm


def create_animation(
    frame_folder: Path,
    animation_folder: Path,
    observable: str,
    animation_type: str,
    time_slice: Optional[int] = None,
    frame_rate: Optional[int] = 10,
) -> None:
    """
    Method for creating animations from generated volumetric figures.

    Args:
        frame_folder: folder path to figures that will be be stitched together.
        animation_folder: folder path to place animations in.
        observable: observable we are creating an animation..
        animation_type: format of animation. Available: 'gif', 'avi' or 'mp4'
        time_slice: optional, eucl time slice.
        frame_rate: frames per second of animation.

    Raises:
        NameError: if animation_type is not recognized.
    """

    # Removes spaces
    observable = observable.replace(" ", "_")

    input_paths = frame_folder / "frame_t%02d.png"

    if time_slice:
        animation_path = animation_folder / (
            f"{observable.lower()}_{time_slice}.{animation_type}"
        )
    else:
        animation_path = animation_folder / (
            f"{observable.lower()}.{animation_type}"
        )

    if animation_type == "gif":
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

    logger.info(f"Running command: {' '.join(cmd)}")

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    _ = proc.stdout.read()  # type: ignore[union-attr]

    logger.success(f"Animation {animation_path} created.")


def plot_iso_surface(
    field: np.ndarray,
    observable_name: str,
    frame_folder: Path,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    n_contours: Optional[int] = 20,
    camera_distance: Optional[float] = 1.0,
    xlabel: Optional[str] = "x",
    ylabel: Optional[str] = "y",
    zlabel: Optional[str] = "z",
    title: Optional["str"] = None,
    figsize: Optional[tuple[int, int]] = (1280, 1280),
) -> None:
    """
    Function for creating figures of volumetric surfaces.

    Args:
        field: field array of size (N,N,N,NT) to plot. The number of
            points to animate over is always the last dimension.
        observable_name: str of observable_name we are plotting.
        frame_folder: location of where to temporary store frames.
        vmin: float lower cutoff value of the field.
        vmax: float upper cutoff value of the field.
        n_contours: optional integer argument for number of contours.
        camera_distance: scalar to multiple camera position by.
        xlabel: x label.
        ylabel: y label.
        zlabel: z label.
        title: title of figure.
        figsize: shape of figure.
    """

    frame_folder.mkdir(exist_ok=True)
    logger.info(f"Folder created at {str(frame_folder)}")

    n_frames, n, _, _ = field.shape

    if vmin is None:
        vmin = np.min(field)

    if vmax is None:
        vmax = np.max(field)

    if title is None and observable_name != "Observable":
        title = observable_name

    # Sets up the contours
    contour_list = np.linspace(vmin, vmax, n_contours)
    contour_list = contour_list.tolist()

    for it in tqdm(range(n_frames), desc=f"Rendering {observable_name}"):

        p = pv.Plotter(window_size=figsize, off_screen=True)
        p.enable_anti_aliasing()
        p.set_background(color="#AFAFAF")

        volume = field[it]

        grid = pv.UniformGrid()
        grid.dimensions = volume.shape

        grid.point_data["values"] = volume.flatten(order="F")
        contour = grid.contour(contour_list)
        outline = grid.outline()

        # Viable color maps:
        # - viridis
        # - plasma
        # - Spectral
        # - coolwarm
        #
        # More color maps seen at:
        # https://matplotlib.org/stable/tutorials/colors/colormaps.html

        p.add_mesh(outline, color="k")
        p.add_mesh(
            contour,
            clim=[vmin, vmax],
            cmap="plasma",
            show_scalar_bar=True,
            opacity=0.65,
            scalar_bar_args={
                "vertical": True,
                "label_font_size": 20,
                "title_font_size": 26,
                "title": "",
                "font_family": "times",
                "fmt": "%.2e",
                "position_y": 0.0125,
            },
        )
        p.show_grid(
            font_size=26,
            font_family="times",
            xlabel=xlabel,
            ylabel=ylabel,
            zlabel=zlabel,
        )
        pos = list(map(lambda f: f * camera_distance, p.camera.position))
        p.set_position(pos)
        p.camera.elevation = -2.5

        p.add_text(
            f"Frame: {it:-02d}",
            font="times",
            font_size=14,
            position="upper_right",
        )
        p.add_text(
            (
                f"Avg={volume.mean():8.2e}\n"
                f"Std={volume.std():8.2e}\n"
                f"Min={volume.min():8.2e}\n"
                f"Max={volume.max():8.2e}"
            ),
            font="times",
            position="lower_left",
            font_size=12,
        )

        if title:
            p.add_title(title, font="times")

        fpath = frame_folder / f"frame_t{it:02d}.png"
        p.screenshot(fpath, return_img=False)

        tqdm.write(f"file created at {fpath}")

    logger.info("Figures created.")
