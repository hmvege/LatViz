import re
from pathlib import Path
from typing import Optional

import numpy as np
from tqdm import tqdm


def check_folder(
    folder: Path, dryrun: bool = False, verbose: bool = False
) -> None:
    """Verifies and creates folder if none exists.

    Args:
        folder (Path): Description
        dryrun (bool, optional): Description
        verbose (bool, optional): Description
    """
    # Checks that figures folder exist, and if not will create it
    if not folder.exists():
        if dryrun or verbose:
            print("> mkdir %s" % folder)
        if not dryrun:
            folder.mkdir()


class _FlowTimeFilter:
    """Selects .bin config with correct flow time."""

    def __init__(self, flow_time: int):
        assert isinstance(flow_time, int)
        self.flow_time = flow_time

    def __call__(self, file_path: Path) -> bool:
        """Function for checking if the correct file has been selected.

        Args:
            file_path (Path): Description

        Returns:
            bool: Description
        """
        # TODO: make sure we can locate any type
        # TODO: redundant once we load an entire folder. Check order instead.
        found_flow_time = re.findall(r"(\d+).bin", str(file_path))
        assert len(found_flow_time) == 1, (
            f"Multiple configs for similar flow time {self.flow_time}:"
            f"\n{found_flow_time}"
        )
        if int(self.flow_time) == int(found_flow_time[0]):
            return True
        else:
            return False


def load_field_from_file(
    file: Path,
    N: int,
    NT: int,
    euclidean_time: Optional[int] = None,
    data_order: str = "F",
):
    """
    Loads field from file.

    Args:
        file (Path): path to .bin file containing lattice data.
        N (int): spatial time.
        NT (int): temporal time.
        euclidean_time (Optional[int], optional): what Euclidean time slice
            to look at. Default is retrieving all Euclidean time slices.
        data_order (str, optional): data structure. Either "C" or "F".
    """
    assert data_order in ["F", "C"], f"Unknown data order type: {data_order}"

    if euclidean_time is None:
        return np.fromfile(file, dtype=float).reshape(
            (N, N, N, NT), order=data_order
        )
    else:

        # Loads euclidean time
        block_size = N ** 3 * 8  # 8 is bytes
        start = euclidean_time * block_size

        with open(file, "rb") as fp:
            fp.seek(start)
            block = fp.read(block_size)
            block = np.frombuffer(block, dtype=np.double)

        return np.array(block).reshape((N, N, N), order=data_order)


def load_folder_data(
    folder: Path,
    N: int,
    NT: int,
    euclidean_time: Optional[int] = None,
    flow_time: Optional[int] = None,
    data_order: str = "F",
):
    """
    Loads folder containing binary data.

    Args:
        folder (Path): Folder containing observable(s).
        N (int): spatial points.
        NT (int): temporal points.
        euclidean_time (Optional[int], optional): euclidean time slice to
            render.
        flow_time (Optional[int], optional): flow time to select and render.
        data_order (str, optional): memory structure of the data. Default is
            Fortran, that is (time, z, y, x).
    """

    assert (euclidean_time is None) ^ (
        flow_time is None
    ), "Either choose Euclidean time of Flow time"

    folder_files = sorted(folder.glob("*.bin"))

    data = []

    if flow_time:
        assert isinstance(flow_time, int)

        _flow_time_filter = _FlowTimeFilter(flow_time)
        _tmp_folder_files = list(filter(_flow_time_filter, folder_files))

        if len(_tmp_folder_files) == 0:
            raise IOError(
                f"No flow data with flow time {flow_time} found among "
                f"following files: \n{', '.join(folder_files)}"
            )

        folder_files = _tmp_folder_files
    else:
        assert isinstance(euclidean_time, int)

    for _f in tqdm(folder_files, desc=f"Reading in data from {folder}"):

        data.append(
            load_field_from_file(
                _f, N, NT, euclidean_time=euclidean_time, data_order=data_order
            )
        )

    # Making sure we return with zeroth axis as the one to animate with.
    if flow_time:
        data = np.rollaxis(data[0], -1, 0)
    else:
        data = np.asarray(data)

    return data
