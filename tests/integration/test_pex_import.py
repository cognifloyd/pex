# Copyright 2022 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

import os.path
import sys
from textwrap import dedent

import colors
import pytest

from pex.common import safe_open
from pex.interpreter import PythonInterpreter
from pex.layout import DEPS_DIR, Layout
from pex.resolve.pex_repository_resolver import resolve_from_pex
from pex.targets import Targets
from pex.testing import make_env, pex_check_output, run_pex_command
from pex.typing import TYPE_CHECKING
from pex.variables import ENV

if TYPE_CHECKING:
    from typing import Any, List, Text


@pytest.mark.parametrize(
    "layout", [pytest.param(layout, id=layout.value) for layout in Layout.values()]
)
@pytest.mark.parametrize(
    "execution_mode_args", [pytest.param([], id="UNZIPPED"), pytest.param(["--venv"], id="VENV")]
)
def test_import_from_pex(
    tmpdir,  # type: Any
    layout,  # type: Layout.Value
    execution_mode_args,  # type: List[str]
):
    # type: (...) -> None

    src = os.path.join(str(tmpdir), "src")
    with safe_open(os.path.join(src, "first_party.py"), "w") as fp:
        fp.write(
            dedent(
                """\
                import colors


                def warn(msg):
                    print(colors.yellow(msg))
                """
            )
        )

    pex_root = os.path.join(str(tmpdir), "pex_root")
    pex = os.path.join(str(tmpdir), "importable.pex")
    is_venv = "--venv" in execution_mode_args

    run_pex_command(
        args=[
            "--pex-root",
            pex_root,
            "--runtime-pex-root",
            pex_root,
            "-D",
            src,
            "ansicolors==1.1.8",
            "-o",
            pex,
            "--layout",
            layout.value,
        ]
        + execution_mode_args,
    ).assert_success()

    def execute_with_pex_on_pythonpath(code):
        # type: (str) -> Text
        return (
            pex_check_output(args=[sys.executable, "-c", code], env=make_env(PYTHONPATH=pex))
            .decode("utf-8")
            .strip()
        )

    # Verify 3rd party code can be imported hermetically from the PEX.
    alternate_pex_root = os.path.join(str(tmpdir), "alternate_pex_root")
    with ENV.patch(PEX_ROOT=alternate_pex_root):
        ambient_sys_path = [
            installed_distribution.fingerprinted_distribution.distribution.location
            for installed_distribution in resolve_from_pex(
                targets=Targets(interpreters=(PythonInterpreter.from_binary(sys.executable),)),
                pex=pex,
                requirements=["ansicolors==1.1.8"],
            ).installed_distributions
        ]

    third_party_path = execute_with_pex_on_pythonpath(
        dedent(
            """\
            # Executor code like the AWS runtime.
            import sys
            
            sys.path = {ambient_sys_path!r} + sys.path
            
            # User code residing in the PEX.
            from __pex__ import colors
            
            print(colors.__file__)
            """.format(
                ambient_sys_path=ambient_sys_path
            )
        )
    )
    if is_venv:
        expected_prefix = os.path.join(pex_root, "venvs")
    elif layout is Layout.LOOSE:
        expected_prefix = os.path.join(pex, DEPS_DIR)
    else:
        expected_prefix = os.path.join(pex_root, "installed_wheels")
    assert third_party_path.startswith(
        expected_prefix
    ), "Expected 3rd party ansicolors path {path} to start with {expected_prefix}".format(
        path=third_party_path, expected_prefix=expected_prefix
    )

    # Verify 1st party code can be imported.
    first_party_path = execute_with_pex_on_pythonpath(
        "from __pex__ import first_party; print(first_party.__file__)"
    )
    if not is_venv and layout is Layout.LOOSE:
        assert os.path.join(pex, "first_party.py") == first_party_path
    else:
        expected_prefix = os.path.join(pex_root, "venvs" if is_venv else "unzipped_pexes")
        assert first_party_path.startswith(
            expected_prefix
        ), "Expected 1st party first_party.py path {path} to start with {expected_prefix}".format(
            path=first_party_path, expected_prefix=expected_prefix
        )

    # Verify a single early import of __pex__ allows remaining imports to be "normal".
    assert "\n".join((colors.blue("42"), colors.yellow("Vogon"))) == execute_with_pex_on_pythonpath(
        dedent(
            """\
            import __pex__

            import colors
            import first_party
            
            
            print(colors.blue("42"))
            first_party.warn("Vogon")
            """
        )
    )
