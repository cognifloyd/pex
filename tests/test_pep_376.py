# Copyright 2022 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).
import os

import pytest

from pex.interpreter import PythonInterpreter
from pex.pep_376 import InstalledFile, find_and_replace_path_components
from pex.typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional


def test_filter_path_invalid():
    # type: () -> None

    with pytest.raises(ValueError):
        find_and_replace_path_components("foo", "bar", "")
        find_and_replace_path_components("foo", "", "baz")


def test_filter_path_noop():
    # type: () -> None

    assert "" == find_and_replace_path_components("", "spam", "eggs")
    assert "." == find_and_replace_path_components(".", "spam", "eggs")
    assert ".." == find_and_replace_path_components("..", "spam", "eggs")
    assert "/" == find_and_replace_path_components("/", "spam", "eggs")
    assert os.path.join("foo", "bar", "baz") == find_and_replace_path_components(
        "foo/bar/baz", "spam", "eggs"
    )


def test_filter_path_basic():
    # type: () -> None

    assert os.path.join("spam", "bar", "baz") == find_and_replace_path_components(
        "foo/bar/baz", "foo", "spam"
    )
    assert os.path.join("foo", "spam", "baz") == find_and_replace_path_components(
        "foo/bar/baz", "bar", "spam"
    )
    assert os.path.join("foo", "bar", "spam") == find_and_replace_path_components(
        "foo/bar/baz", "baz", "spam"
    )


def test_filter_path_absolute():
    # type: () -> None

    assert os.path.join("/spam", "bar", "baz") == find_and_replace_path_components(
        "/foo/bar/baz", "foo", "spam"
    )


def test_filter_path_relative():
    # type: () -> None

    assert os.path.join("..", "spam", "bar", "baz") == find_and_replace_path_components(
        "../foo/bar/baz", "foo", "spam"
    )
    assert os.path.join(".", "spam", "bar", "baz") == find_and_replace_path_components(
        "./foo/bar/baz", "foo", "spam"
    )
    assert os.path.join("/spam", "..", "bar", ".", "baz") == find_and_replace_path_components(
        "/foo/../bar/./baz", "foo", "spam"
    )


def test_installed_file_path_normalization_noop(
    py37,  # type: PythonInterpreter
    py310,  # type: PythonInterpreter
):
    # type: (...) -> None

    def assert_noop(interpreter=None):
        # type: (Optional[PythonInterpreter]) -> None
        assert os.path.join("foo", "bar") == InstalledFile.normalized_path(
            "foo/bar", interpreter=interpreter
        )
        assert os.path.join("foo", "python2.0") == InstalledFile.normalized_path(
            "foo/python2.0", interpreter=interpreter
        )
        assert os.path.join("foo", "bar") == InstalledFile.denormalized_path(
            "foo/bar", interpreter=interpreter
        )

    assert_noop()
    assert_noop(py37)
    assert_noop(py310)


def test_installed_file_path_normalization_nominal(
    py37,  # type: PythonInterpreter
    py310,  # type: PythonInterpreter
):
    # type: (...) -> None

    assert os.path.join("foo", "pythonX.Y", "bar") == InstalledFile.normalized_path(
        "foo/python3.7/bar", interpreter=py37
    )
    assert os.path.join("foo", "pythonX.Y", "bar") == InstalledFile.normalized_path(
        "foo/python3.10/bar", interpreter=py310
    )

    assert os.path.join("foo", "python3.7", "bar") == InstalledFile.denormalized_path(
        "foo/pythonX.Y/bar", interpreter=py37
    )
    assert os.path.join("foo", "python3.10", "bar") == InstalledFile.denormalized_path(
        "foo/pythonX.Y/bar", interpreter=py310
    )
