# Copyright 2021 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import absolute_import

from pex.jobs import DEFAULT_MAX_JOBS
from pex.network_configuration import NetworkConfiguration
from pex.pip import ResolverVersion
from pex.typing import TYPE_CHECKING

if TYPE_CHECKING:
    import attr  # vendor:skip
    from typing import Tuple
else:
    from pex.third_party import attr


PYPI = "https://pypi.org/simple"


@attr.s(frozen=True)
class PipConfiguration(object):
    resolver_version = attr.ib(default=ResolverVersion.PIP_LEGACY)  # type: ResolverVersion.Value
    indexes = attr.ib(default=(PYPI,), converter=tuple)  # type: Tuple[str, ...]
    find_links = attr.ib(default=(), converter=tuple)  # type: Tuple[str, ...]
    network_configuration = attr.ib(default=NetworkConfiguration())  # type: NetworkConfiguration
    allow_prereleases = attr.ib(default=False)  # type: bool
    allow_wheels = attr.ib(default=True)  # type: bool
    allow_builds = attr.ib(default=True)  # type: bool
    transitive = attr.ib(default=True)  # type: bool
    max_jobs = attr.ib(default=DEFAULT_MAX_JOBS)  # type: int


@attr.s(frozen=True)
class PexRepositoryConfiguration(object):
    pex_repository = attr.ib()  # type: str
    network_configuration = attr.ib(default=NetworkConfiguration())  # type: NetworkConfiguration
    transitive = attr.ib(default=True)  # type: bool