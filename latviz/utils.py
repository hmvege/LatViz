import re
from pathlib import Path
from typing import Optional

import numpy as np
from loguru import logger
from tqdm import tqdm


def load_field_from_file(
    file: Path,
    n: int,
    nt: int,
    euclidean_time: Optional[int] = None,
) -> np.ndarray:
    """
    Loads field from file.

    Args:
        file (Path): path to .bin file containing lattice data.
        n (int): spatial time.
        nt (int): temporal time.
        euclidean_time (Optional[int], optional): what Euclidean time slice
            to look at. Default is retrieving all Euclidean time slices.
    """
    if euclidean_time is None:
        return np.fromfile(file, dtype=float).reshape((n, n, n, nt), order="F")
    else:

        # Loads euclidean time
        block_size = n ** 3 * 8  # 8 is bytes
        start = euclidean_time * block_size

        with open(file, "rb") as fp:
            fp.seek(start)
            block = fp.read(block_size)
            block = np.frombuffer(block, dtype=np.double)

        return np.array(block).reshape((n, n, n), order="F")


def _check_file_sorting(observable_config_path: list[Path]) -> None:
    """Checks the order of input files."""
    _names = list(map(lambda f: f.name, observable_config_path))
    _names_sorted = list(
        sorted(_names, key=lambda f: re.findall(r"(\d+).bin", f)[0])
    )
    _is_match = [f0 == f1 for f0, f1 in zip(_names, _names_sorted)]
    if sum(_is_match) != len(_is_match):
        logger.warning("Possible unsorted input files detected. Continuing.")


def load_fields(
    observable_config_path: list[Path],
    n: int,
    nt: int,
    time_slice: Optional[int] = None,
) -> np.ndarray:
    """Load data from provided path(s).

    Assumes a input configurations is a hypercube of shape (n, n, n, nt) on
    fortran ordering, i.e. column-major ordering.

    Args:
        observable_config_path (list(Path)): List of paths containing
            observable(s) of configurations.
        n (int): spatial points.
        nt (int): temporal points.
        time_slice (Optional[int], optional): time slice to render.

    Raises:
        ValueError: if selected time slice exceeds temporal dimension.

    Returns:
        hypercube with the axis to animate over as the first axis.
    """

    if len(observable_config_path) > 1:
        _check_file_sorting(observable_config_path)

        if time_slice is None:
            raise ValueError(
                "Multiple observable configurations"
                f"(={len(observable_config_path)}) require a time "
                f"slice(={time_slice})."
            )

        if time_slice is not None and time_slice >= nt:
            raise ValueError(
                f"time_slice={time_slice} is greater or equal than the"
                f" temporal dimension nt={nt}"
            )
    elif len(observable_config_path) == 1:
        if time_slice is not None:
            raise ValueError(
                "Cannot animate from a single field configuration at a given"
                f" time slice(={time_slice})."
            )
    else:
        raise ValueError("No configurations provided.")

    data = []

    for field_path in tqdm(
        observable_config_path,
        desc=f"Reading in data from {len(observable_config_path)} files."
    ):
        tqdm.write(f"{str(field_path)}")
        data.append(
            load_field_from_file(field_path, n, nt, euclidean_time=time_slice)
        )

    # Making sure we return with zeroth axis as the one to animate with.
    if len(observable_config_path) == 1:
        data = np.rollaxis(data[0], -1, 0)
    else:
        data = np.asarray(data)

    return data
