import enum

__copyright__ = "Copyright 2020-2021, Gispo Ltd"
__license__ = "GPL version 3"
__email__ = "info@gispo.fi"
__revision__ = "$Format:%H$"

import logging
from typing import TYPE_CHECKING, Optional, Union, cast

from qgis.core import (
    Qgis,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextScope,
    QgsExpressionContextUtils,
    QgsFeature,
    QgsGeometry,
    QgsMapLayer,
    QgsUnitTypes,
    QgsVectorLayer,
    QgsWkbTypes,
)

from .custom_logging import bar_msg
from .exceptions import QgsPluginExpressionException
from .i18n import tr

if TYPE_CHECKING:
    from qgis.core import QgsVectorLayerTemporalProperties

LOGGER = logging.getLogger(__name__)

POINT_TYPES = {
    QgsWkbTypes.Type.Point,
    QgsWkbTypes.Type.MultiPoint,
}

LINE_TYPES = {
    QgsWkbTypes.Type.LineString,
    QgsWkbTypes.Type.MultiLineString,
}
POLYGON_TYPES = {
    QgsWkbTypes.Type.Polygon,
    QgsWkbTypes.Type.MultiPolygon,
    QgsWkbTypes.Type.CurvePolygon,
}


@enum.unique
class LayerType(enum.Enum):
    Point = {"wkb_types": POINT_TYPES}
    Line = {"wkb_types": LINE_TYPES}
    Polygon = {"wkb_types": POLYGON_TYPES}
    Unknown: dict[str, set[QgsWkbTypes.Type]] = {"wkb_types": set()}

    @staticmethod
    def from_wkb_type(wkb_type: QgsWkbTypes.Type) -> "LayerType":
        return next(
            (
                l_type
                for l_type in LayerType
                if QgsWkbTypes.flatType(wkb_type) in l_type.wkb_types
            ),
            LayerType.Unknown,
        )

    @staticmethod
    def from_layer(layer: QgsVectorLayer) -> "LayerType":
        return LayerType.from_wkb_type(layer.wkbType())

    @staticmethod
    def from_geometry(geometry: QgsGeometry) -> "LayerType":
        return LayerType.from_wkb_type(geometry.wkbType())

    @property
    def wkb_types(self) -> set[QgsWkbTypes.Type]:
        return self.value["wkb_types"]


def set_temporal_settings(
    layer: QgsVectorLayer,
    dt_field: str,
    time_step: int,
    unit: Optional["QgsUnitTypes.TemporalUnit"] = None,
) -> None:
    """
    Set temporal settings for vector layer temporal range for raster layer
    :param layer: raster layer
    :param dt_field: name of the date time field
    :param time_step: time step in some QgsUnitTypes.TemporalUnit
    :param unit: QgsUnitTypes.TemporalUnit
    """
    tprops = cast("QgsVectorLayerTemporalProperties", layer.temporalProperties())
    tprops.setMode(Qgis.VectorTemporalMode.FeatureDateTimeInstantFromField)

    tprops.setStartField(dt_field)
    tprops.setFixedDuration(time_step)
    tprops.setDurationUnits(unit or QgsUnitTypes.TemporalUnit.TemporalMinutes)
    tprops.setIsActive(True)


def evaluate_expressions(
    exp: QgsExpression,
    feature: Optional[QgsFeature] = None,
    layer: Optional[QgsMapLayer] = None,
    context_scopes: Optional[list[QgsExpressionContextScope]] = None,
) -> Union[bool, int, str, float, None]:
    """
    Evaluate a QGIS expression
    :param exp: QGIS expression
    :param feature: Optional QgsFeature
    :param layer: Optional QgsMapLayer
    :param context_scopes: Optional list of QgsExpressionContextScopes
    :return: evaluated value of the expression
    """
    context = QgsExpressionContext()
    scopes = context_scopes if context_scopes is not None else []

    if layer:
        scopes.append(QgsExpressionContextUtils.layerScope(layer))
    context.appendScopes(scopes)
    if feature:
        context.setFeature(feature)

    value: Union[bool, int, str, float, None] = exp.evaluate(context)
    if exp.hasParserError():
        raise QgsPluginExpressionException(bar_msg=bar_msg(exp.parserErrorString()))

    if exp.hasEvalError():
        raise QgsPluginExpressionException(bar_msg=bar_msg(exp.evalErrorString()))
    return value


def get_field_index(layer: QgsVectorLayer, field_name: str) -> int:
    """
    Get field index if exists
    :param layer: QgsVectorLayer
    :param field_name: name of the field
    :return: index of the field
    """
    field_index = layer.fields().indexFromName(field_name)
    if field_index == -1:
        raise KeyError(
            tr(
                "Field name {} does not exist in layer {}",
                field_name,
                layer.name(),
            )
        )
    return field_index
