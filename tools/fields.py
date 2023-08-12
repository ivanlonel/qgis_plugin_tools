from typing import Union

from qgis.core import QgsApplication, QgsFields
from qgis.gui import QgsDateTimeEdit, QgsDoubleSpinBox, QgsSpinBox
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QCheckBox, QComboBox, QDateEdit, QWidget

__copyright__ = "Copyright 2020-2021, Gispo Ltd"
__license__ = "GPL version 3"
__email__ = "info@gispo.fi"
__revision__ = "$Format:%H$"


# noinspection PyCallByClass,PyArgumentList
def variant_type_icon(field_type: QVariant) -> QIcon:
    type_icons = {
        QVariant.Type.Bool: "/mIconFieldBool.svg",
        QVariant.Type.Int: "/mIconFieldInteger.svg",
        QVariant.Type.UInt: "/mIconFieldInteger.svg",
        QVariant.Type.LongLong: "/mIconFieldInteger.svg",
        QVariant.Type.ULongLong: "/mIconFieldInteger.svg",
        QVariant.Type.Double: "/mIconFieldFloat.svg",
        QVariant.Type.String: "/mIconFieldText.svg",
        QVariant.Type.Date: "/mIconFieldDate.svg",
        QVariant.Type.DateTime: "/mIconFieldTime.svg",
        QVariant.Type.Time: "/mIconFieldTime.svg",
        QVariant.Type.ByteArray: "/mIconFieldBinary.svg",
    }
    file_name = type_icons.get(field_type)
    if file_name is None:
        return QIcon()
    return QgsApplication.getThemeIcon(file_name)


def widget_for_field(field_type: QVariant) -> QWidget:
    if field_type == QVariant.Type.Bool:
        return QCheckBox()
    if field_type in {
        QVariant.Type.Int,
        QVariant.Type.UInt,
        QVariant.Type.LongLong,
        QVariant.Type.ULongLong,
    }:
        spin_box = QgsSpinBox()
        spin_box.setMaximum(2147483647)
        return spin_box
    if field_type == QVariant.Type.Double:
        spin_box = QgsDoubleSpinBox()
        spin_box.setMaximum(2147483647)
        return spin_box
    if field_type == QVariant.Type.Date:
        return QDateEdit()
    if field_type in {QVariant.Type.DateTime, QVariant.Type.Time}:
        return QgsDateTimeEdit()

    # QVariant.Type.ByteArray, QVariant.Type.String or other
    q_combo_box = QComboBox()
    q_combo_box.setEditable(True)
    return q_combo_box


def value_for_widget(widget: type[QWidget]) -> Union[str, bool, float, int]:
    if isinstance(widget, QComboBox):
        return widget.currentText()
    if isinstance(widget, QCheckBox):
        return widget.isChecked()
    if isinstance(widget, QgsDateTimeEdit):
        return widget.dateTime().toString("yyyy-MM-dd hh:mm:ss")
    if isinstance(widget, (QgsSpinBox, QgsDoubleSpinBox)):
        return widget.value()
    return str(widget.text())


def provider_fields(fields: QgsFields) -> QgsFields:
    flds = QgsFields()
    for i in range(fields.count()):
        if fields.fieldOrigin(i) == QgsFields.OriginProvider:
            flds.append(fields.at(i))
    return flds
