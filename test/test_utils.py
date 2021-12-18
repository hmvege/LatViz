import logging
import tempfile
from pathlib import Path

import numpy as np
import pytest
from _pytest.logging import caplog as _caplog
from loguru import logger

from latviz.utils import load_field_from_file, load_fields, _check_file_sorting


@pytest.fixture
def caplog(_caplog):
    """Helper class for verifying warning message."""
    class PropagateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)
    handler_id = logger.add(
        PropagateHandler(), format="{message} {extra}", level="TRACE"
    )
    yield _caplog
    logger.remove(handler_id)


def create_dummy_field(
    n: int, nt: int, folder: Path, name: str = "field"
) -> tuple[Path, np.ndarray]:
    """
    Creates a dummy field in a folder and returns the path.
    """
    field = np.random.randn(nt, n, n, n)

    field_path = folder / f"{name}.bin"

    with open(field_path, "wb") as f:
        f.write(field.tobytes(order="C"))
    logger.info(f"Wrote {field_path}")

    return field_path, field


@pytest.mark.parametrize(
    "time_slice,n,nt",
    [(None, 32, 64), (None, 16, 32), (0, 32, 64), (40, 32, 64)]
)
def test_load_field_from_file(time_slice, n, nt):
    """Test for loading a field."""
    folder = tempfile.TemporaryDirectory(suffix="_fields")

    field_path, field = create_dummy_field(n, nt, Path(folder.name))
    logger.info("field.shape:", field.shape)
    logger.info(f"field value at (0,0,0,0)={field[0, 0, 0, 0]}")
    logger.info(f"field value at (0,0,0,10)={field[0, 0, 0, 10]}")

    if time_slice is not None:
        field = field[time_slice]

    loaded_data = load_field_from_file(field_path, n, nt, time_slice)
    logger.info("loaded_data.shape:", loaded_data.shape)

    if len(loaded_data.shape) == 4:
        loaded_data = np.rollaxis(loaded_data, -1, 0)
        loaded_data = np.rollaxis(loaded_data, 3, 1)
        loaded_data = np.rollaxis(loaded_data, -1, 2)
        logger.info(f"loaded_data value at (0,0,0,0)={field[0, 0, 0, 0]}")
        logger.info(f"loaded_data value at (0,0,0,10)={field[0, 0, 0, 10]}")
    else:
        loaded_data = np.rollaxis(loaded_data, -1, 0)
        loaded_data = np.rollaxis(loaded_data, 2, 1)
        logger.info(f"loaded_data value at (0,0,0)={field[0, 0, 0]}")

    logger.info("field.shape:", field.shape)
    logger.info("loaded_data.shape:", loaded_data.shape)

    folder.cleanup()
    assert np.array_equal(field, loaded_data)


def test__check_file_sorting(caplog):
    """Test for verifying the file sorting."""

    test_paths = [Path(f"field_{i:04d}.bin") for i in range(100)]

    _check_file_sorting(test_paths)
    test_paths_switched = test_paths
    test_paths_switched[3] = test_paths[6]
    test_paths_switched[6] = test_paths[3]

    _check_file_sorting(test_paths)

    assert caplog.record_tuples[0][1] == 30
    assert (
        "Possible unsorted input files detected. Continuing."
    ) in caplog.record_tuples[0][2]


@pytest.mark.parametrize(
    "n_fields,n,nt,time_slice",
    [
        (0, 16, 32, 40),
        (1, 16, 32, 1),
        (10, 16, 32, 40),
        (10, 32, 64, 64),
        (20, 32, 64, None),
        (50, 16, 32, None),
    ]
)
def test_load_fields_exceptions(n_fields, n, nt, time_slice):
    """Test for verifying that certain exceptions is raised in load_fields."""
    folder = tempfile.TemporaryDirectory(suffix="_fields")

    fields = [
        create_dummy_field(n, nt, Path(folder.name), name=f"field_{i:03d}")
        for i in range(n_fields)
    ]
    field_paths = [i for i, j in fields]
    fields = [j for i, j in fields]

    if n_fields > 1 and time_slice is None:
        with pytest.raises(ValueError) as exception_info:
            _ = load_fields(
                field_paths, n, nt, time_slice=time_slice
            )
            msg = (
                "Multiple observable configurations"
                f"(={n_fields}) require a time slice(={time_slice})."
            )
            assert msg in str(exception_info.value)
    elif n_fields > 1 and time_slice >= nt:
        with pytest.raises(ValueError) as exception_info:
            _ = load_fields(
                field_paths, n, nt, time_slice=time_slice
            )
            msg = (
                f"time_slice={time_slice} is greater or equal than the"
                f" temporal dimension nt={nt}"
            )
            assert msg in str(exception_info.value)
    elif n_fields == 1 and time_slice is not None:
        with pytest.raises(ValueError) as exception_info:
            _ = load_fields(
                field_paths, n, nt, time_slice=time_slice
            )
            msg = (
                "Cannot animate from a single field configuration at a given"
                f" time slice(={time_slice})."
            )
            assert msg in str(exception_info.value)
    else:
        with pytest.raises(ValueError) as exception_info:
            _ = load_fields(
                field_paths, n, nt, time_slice=time_slice
            )
            assert "No configurations provided." in str(exception_info.value)

    folder.cleanup()


@pytest.mark.parametrize(
    "n_fields,n,nt,time_slice",
    [
        (1, 32, 64, None),
        (1, 16, 32, None),
        (30, 32, 64, 0),
        (10, 32, 64, 40),
    ]
)
def test_load_fields(n_fields, n, nt, time_slice):
    """Test for loading multiple fields."""
    folder = tempfile.TemporaryDirectory(suffix="_fields")

    fields = [
        create_dummy_field(n, nt, Path(folder.name), name=f"field_{i:03d}")
        for i in range(n_fields)
    ]
    field_paths = [i for i, j in fields]
    if time_slice is not None:
        fields = [j[time_slice] for i, j in fields]
    else:
        fields = [j for i, j in fields]

    loaded_fields = load_fields(field_paths, n, nt, time_slice=time_slice)

    if n_fields == 1:
        loaded_data = np.rollaxis(loaded_fields, 3, 1)
        loaded_data = np.rollaxis(loaded_data, -1, 2)
        assert np.array_equal(fields[0], loaded_data)
    else:
        for field, loaded_data in zip(fields, loaded_fields):
            loaded_data = np.rollaxis(loaded_data, -1, 0)
            loaded_data = np.rollaxis(loaded_data, 2, 1)
            assert np.array_equal(field, loaded_data)

    folder.cleanup()
