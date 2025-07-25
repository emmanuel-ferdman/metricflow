"""Contains input classes for the query resolver.

The naming of these classes is a little odd as they have the "For.." suffix. But using the "*ResolverInput" leads to
some confusing names like "ResolverInputForQuery" -> "QueryResolverInput". Improved naming for these classes is TBD.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Union

from dbt_semantic_interfaces.protocols import WhereFilterIntersection
from typing_extensions import override

from metricflow_semantics.helpers.string_helpers import mf_indent
from metricflow_semantics.mf_logging.pretty_print import mf_pformat
from metricflow_semantics.naming.naming_scheme import QueryItemNamingScheme
from metricflow_semantics.protocols.query_parameter import (
    GroupByQueryParameter,
    MetricQueryParameter,
    OrderByQueryParameter,
)
from metricflow_semantics.query.group_by_item.resolution_path import MetricFlowQueryResolutionPath
from metricflow_semantics.query.resolver_inputs.base_resolver_inputs import (
    InputPatternDescription,
    MetricFlowQueryResolverInput,
)
from metricflow_semantics.specs.patterns.spec_pattern import SpecPattern


@dataclass(frozen=True)
class InvalidStringInput(MetricFlowQueryResolverInput):
    """A string input that doesn't match any of the known naming schemes."""

    input_obj: str

    @property
    @override
    def ui_description(self) -> str:
        return self.input_obj


@dataclass(frozen=True)
class ResolverInputForMetric(MetricFlowQueryResolverInput):
    """An input that describes the metrics in the query."""

    input_obj: Union[MetricQueryParameter, str]
    naming_scheme: QueryItemNamingScheme
    spec_pattern: SpecPattern
    alias: Optional[str] = None

    @property
    @override
    def ui_description(self) -> str:
        return str(self.input_obj)

    @property
    @override
    def input_pattern_description(self) -> InputPatternDescription:
        return InputPatternDescription(
            naming_scheme=self.naming_scheme,
            spec_pattern=self.spec_pattern,
        )


@dataclass(frozen=True)
class ResolverInputForGroupByItem(MetricFlowQueryResolverInput):
    """An input that describes a group-by item in the query."""

    input_obj: Union[GroupByQueryParameter, str]
    input_obj_naming_scheme: QueryItemNamingScheme
    spec_pattern: SpecPattern
    alias: Optional[str] = None

    @property
    @override
    def ui_description(self) -> str:
        return str(self.input_obj)

    @property
    @override
    def input_pattern_description(self) -> InputPatternDescription:
        return InputPatternDescription(
            naming_scheme=self.input_obj_naming_scheme,
            spec_pattern=self.spec_pattern,
        )


@dataclass(frozen=True)
class ResolverInputForOrderByItem(MetricFlowQueryResolverInput):
    """An input that describes the ordered item.

    The challenge with order-by items is that it may not be obvious how to match an order-by item to a metric or a
    group-by item in the query. When the query inputs were always strings, this was easy because the order-by item
    could be resolved with an equality check. However, when the query inputs could be a string or a *QueryParameter
    object, the equality check is not possible. e.g. consider the case:

        group-by item: TimeDimension("creation_time"), order-by item: "creation_time".

    Instead, the approach is to resolve the metrics / group-by items into concrete spec objects, and then use the
    SpecPattern generated from the order-by item input to match to those.

    possible_inputs is necessary because at parse-time for string inputs, order-by inputs are resolved to spec patterns,
    and those patterns could match to either metrics or group-by-items.
    """

    input_obj: Union[str, OrderByQueryParameter]
    possible_inputs: Tuple[Union[ResolverInputForMetric, ResolverInputForGroupByItem], ...]
    descending: bool

    @property
    @override
    def ui_description(self) -> str:
        return str(self.input_obj)


@dataclass(frozen=True)
class ResolverInputForLimit(MetricFlowQueryResolverInput):
    """An input that describes the limit."""

    limit: Optional[int]

    @property
    @override
    def ui_description(self) -> str:
        return str(self.limit)


@dataclass(frozen=True)
class ResolverInputForMinMaxOnly(MetricFlowQueryResolverInput):
    """An input that describes if the query will be aggregated to only the min and max."""

    min_max_only: bool = False

    @property
    @override
    def ui_description(self) -> str:
        return str(self.min_max_only)


@dataclass(frozen=True)
class ResolverInputForApplyGroupBy(MetricFlowQueryResolverInput):
    """An input that describes if the query will apply a group by. Can only be false for no-metric queries."""

    apply_group_by: bool = True

    @property
    @override
    def ui_description(self) -> str:
        return str(self.apply_group_by)


@dataclass(frozen=True)
class ResolverInputForQueryLevelWhereFilterIntersection(MetricFlowQueryResolverInput):
    """An input that describes the where filter for the query."""

    where_filter_intersection: WhereFilterIntersection

    @property
    @override
    def ui_description(self) -> str:
        return (
            "WhereFilter(\n"
            + mf_indent(
                mf_pformat(
                    [where_filter.where_sql_template for where_filter in self.where_filter_intersection.where_filters]
                )
            )
            + "\n)"
        )


@dataclass(frozen=True)
class ResolverInputForWhereFilterIntersection(MetricFlowQueryResolverInput):
    """An input to describe a where filter anywhere in the resolution DAG.

    This can represent a query-level where filter, or one that is in a metric definition. Treating the defined filters
    as a resolver input so that it can go through the same error flows as the other query inputs.
    """

    where_filter_intersection: WhereFilterIntersection
    filter_resolution_path: MetricFlowQueryResolutionPath
    # e.g. TimeDimension('metric_time'), but may not be available if filter has parsing errors.
    object_builder_str: Optional[str]

    @property
    @override
    def ui_description(self) -> str:
        lines = [
            "WhereFilter(",
            mf_indent(
                mf_pformat(
                    [where_filter.where_sql_template for where_filter in self.where_filter_intersection.where_filters]
                )
            ),
            ")",
            "Filter Path:",
            mf_indent(self.filter_resolution_path.ui_description),
        ]
        if self.object_builder_str is not None:
            lines.append("Object Builder Input:")
            lines.append(mf_indent(self.object_builder_str))
        return "\n".join(lines)


@dataclass(frozen=True)
class ResolverInputForQuery(MetricFlowQueryResolverInput):
    """An input that describes the entire query."""

    metric_inputs: Tuple[ResolverInputForMetric, ...]
    group_by_item_inputs: Tuple[ResolverInputForGroupByItem, ...]
    filter_input: ResolverInputForQueryLevelWhereFilterIntersection
    order_by_item_inputs: Tuple[ResolverInputForOrderByItem, ...]
    limit_input: ResolverInputForLimit
    min_max_only: ResolverInputForMinMaxOnly
    apply_group_by: ResolverInputForApplyGroupBy

    @property
    @override
    def ui_description(self) -> str:
        # Since the error message shows the query in the resolution path and there's only ever 1 query for an error
        # message, there's no need for a query-specific description.
        return ""
