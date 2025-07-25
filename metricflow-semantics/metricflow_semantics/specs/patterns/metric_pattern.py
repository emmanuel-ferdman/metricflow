from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from dbt_semantic_interfaces.references import MetricReference
from typing_extensions import override

from metricflow_semantics.specs.instance_spec import InstanceSpec
from metricflow_semantics.specs.metric_spec import MetricSpec
from metricflow_semantics.specs.patterns.spec_pattern import SpecPattern
from metricflow_semantics.specs.spec_set import group_specs_by_type


@dataclass(frozen=True)
class MetricSpecPattern(SpecPattern):
    """Matches MetricSpecs that have the given metric_reference."""

    metric_reference: MetricReference
    descending: Optional[bool] = None

    @override
    def match(self, candidate_specs: Sequence[InstanceSpec]) -> Sequence[MetricSpec]:
        spec_set = group_specs_by_type(candidate_specs)
        return tuple(
            metric_name for metric_name in spec_set.metric_specs if metric_name.reference == self.metric_reference
        )
