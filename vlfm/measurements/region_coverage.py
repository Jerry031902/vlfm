# Copyright (c) 2024. All rights reserved.

from dataclasses import dataclass
from typing import Any, List

import numpy as np
from habitat import registry
from habitat.config.default_structured_configs import (
    MeasurementConfig,
)
from habitat.core.embodied_task import Measure
from habitat.core.simulator import Simulator
from hydra.core.config_store import ConfigStore
from omegaconf import DictConfig


@registry.register_measure
class RegionCoverage(Measure):
    """Measures how much of a target region the agent has explored.

    Need to replace update_metric() logic with real coverage computation later.
    """

    cls_uuid: str = "region_coverage"

    def __init__(
        self, sim: Simulator, config: DictConfig, *args: Any, **kwargs: Any
    ) -> None:
        self._sim = sim
        self._config = config
        # TODO: need load ground-truth region boundaries from MP3D .house file
        super().__init__(*args, **kwargs)

    @staticmethod
    def _get_uuid(*args: Any, **kwargs: Any) -> str:
        return RegionCoverage.cls_uuid

    def reset_metric(self, *args: Any, **kwargs: Any) -> None:
        # TODO: reset coverage grid for new episode
        self._step_count = 0
        self.update_metric()

    def update_metric(self, *args: Any, **kwargs: Any) -> None:
        # just count steps for now to confirm Habitat is calling this
        self._step_count += 1
        # TODO: replace with real coverage fraction (0.0 to 1.0)
        self._metric = self._step_count


@dataclass
class RegionCoverageMeasurementConfig(MeasurementConfig):
    type: str = RegionCoverage.__name__


cs = ConfigStore.instance()
cs.store(
    package="habitat.task.measurements.region_coverage",
    group="habitat/task/measurements",
    name="region_coverage",
    node=RegionCoverageMeasurementConfig,
)