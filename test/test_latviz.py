import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest
from click.testing import CliRunner
from loguru import logger

from test_utils import create_dummy_field
from latviz.latviz import create_animation, plot_iso_surface
from latviz.cli import latviz


runner = CliRunner()


def create_dummy_frame(
    figsize: tuple[int, int], folder: Path, name: str
) -> Path:
    """Creates dummy frame"""
    img = np.random.randn(*figsize)

    fig_path = folder / f"{name}.png"

    fig, ax = plt.subplots(1, 1)
    plt.imshow(img)
    plt.savefig(fig_path)
    plt.close(fig)
    logger.info(f"Wrote {fig_path}")

    return fig_path


def create_dummy_cube(n: int) -> np.ndarray:
    """Creates dummy cube"""
    cube = np.random.randn(n, n, n)
    return cube


@pytest.mark.parametrize(
    "animation_type", [("gif"), ("mp4"), ("avi"), ("failtest")]
)
def test_create_animation(animation_type: str):
    """Validation test of the animation commands."""
    frame_folder = tempfile.TemporaryDirectory(suffix="_frames")
    animation_folder = tempfile.TemporaryDirectory(suffix="_animations")

    frame_folder_path = Path(frame_folder.name)
    animation_folder_path = Path(animation_folder.name)

    observable = "observable"

    if animation_type == "failtest":
        with pytest.raises(NameError) as exception_info:
            create_animation(
                frame_folder_path,
                animation_folder_path,
                observable,
                animation_type,
            )
            msg = f"{animation_type} is not a recognized animation type."
            assert msg in str(exception_info.value)
    else:
        animation_path = animation_folder_path / (
            f"{observable.lower()}.{animation_type}"
        )

        n_dummy_frames = 30
        figsize = (800, 800)

        for i in range(n_dummy_frames):
            create_dummy_frame(figsize, frame_folder_path, f"frame_t{i:02d}")

        create_animation(
            frame_folder_path,
            animation_folder_path,
            observable,
            animation_type,
        )
        assert animation_path.exists()

    frame_folder.cleanup()
    animation_folder.cleanup()


def test_plot_iso_surface():
    """Validation test on the plotting."""
    frame_folder = tempfile.TemporaryDirectory(suffix="_frames")

    frame_folder_path = Path(frame_folder.name)

    n_cubes = 10
    n = 32

    observable_name = "test_obs"
    field = np.random.randn(n_cubes, n, n, n)

    plot_iso_surface(field, observable_name, frame_folder_path)

    for it in range(n_cubes):
        fpath = frame_folder_path / f"frame_t{it:02d}.png"
        assert fpath.exists()

    frame_folder.cleanup()


@pytest.mark.parametrize(
    "n_fields", [(1), (10)]
)
def test_latviz_cli(n_fields):
    """Runs a validation test."""
    frames_folder = tempfile.TemporaryDirectory(suffix="_frames")
    output_folder = tempfile.TemporaryDirectory(suffix="_output")
    output_folder_path = Path(output_folder.name)
    animation_type = "avi"
    n = 32
    nt = 64
    observable = "obs"

    fields = [
        create_dummy_field(
            n, nt, Path(frames_folder.name), name=f"field_{i:03d}"
        )
        for i in range(n_fields)
    ]
    field_paths = [i for i, j in fields]

    if n_fields == 1:
        response = runner.invoke(
            latviz,
            [
                *[str(f) for f in field_paths],
                "-n",
                f"{n}",
                "-nt",
                f"{nt}",
                "-o",
                f"{str(output_folder_path)}",
                "-a",
                f"{animation_type}",
                "-m",
                f"{observable}"
            ]
        )
    else:
        time_slice = 20
        response = runner.invoke(
            latviz,
            [
                *[str(f) for f in field_paths],
                "-n",
                f"{n}",
                "-nt",
                f"{nt}",
                "-t",
                f"{time_slice}",
                "-o",
                f"{str(output_folder_path)}",
                "-a",
                f"{animation_type}",
                "-m",
                f"{observable}"
            ]
        )

    assert response.exit_code == 0

    found_animations = list(output_folder_path.rglob(f"*{animation_type}"))
    assert len(found_animations) == 1
    if n_fields != 1:
        output_animation_name = f"{observable}_{time_slice}.{animation_type}"
    else:
        output_animation_name = f"{observable}.{animation_type}"
    assert found_animations[0].name == output_animation_name

    output_folder.cleanup()
    frames_folder.cleanup()
