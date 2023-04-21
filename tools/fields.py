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
    if field_type == QVariant.Type.Bool:
        return QgsApplication.getThemeIcon("/mIconFieldBool.svg")
    elif field_type in [
        QVariant.Type.Int,
        QVariant.Type.UInt,
        QVariant.Type.LongLong,
        QVariant.Type.ULongLong,
    ]:
        return QgsApplication.getThemeIcon("/mIconFieldInteger.svg")
    elif field_type == QVariant.Type.Double:
        return QgsApplication.getThemeIcon("/mIconFieldFloat.svg")
    elif field_type == QVariant.Type.String:
        return QgsApplication.getThemeIcon("/mIconFieldText.svg")
    elif field_type == QVariant.Type.Date:
        return QgsApplication.getThemeIcon("/mIconFieldDate.svg")
    elif field_type == QVariant.Type.DateTime:
        return QgsApplication.getThemeIcon("/mIconFieldDateTime.svg")
    elif field_type == QVariant.Type.Time:
        return QgsApplication.getThemeIcon("/mIconFieldTime.svg")
    elif field_type == QVariant.Type.ByteArray:
        return QgsApplication.getThemeIcon("/mIconFieldBinary.svg")
    else:
        return QIcon()


def widget_for_field(field_type: QVariant) -> QWidget:
    q_combo_box = QComboBox()
    q_combo_box.setEditable(True)

    if field_type == QVariant.Type.Bool:
        return QCheckBox()
    elif field_type in [
        QVariant.Type.Int,
        QVariant.Type.UInt,
        QVariant.Type.LongLong,
        QVariant.Type.ULongLong,
    ]:
        spin_box = QgsSpinBox()
        spin_box.setMaximum(2147483647)
        return spin_box
    elif field_type == QVariant.Type.Double:
        spin_box = QgsDoubleSpinBox()
        spin_box.setMaximum(2147483647)
        return spin_box
    elif field_type == QVariant.Type.String:
        return q_combo_box
    elif field_type == QVariant.Type.Date:
        return QDateEdit()
    elif field_type == QVariant.Type.DateTime:
        return QgsDateTimeEdit()
    elif field_type == QVariant.Type.Time:
        return QgsDateTimeEdit()
    elif field_type == QVariant.Type.ByteArray:
        return q_combo_box
    else:
        return q_combo_box


def value_for_widget(widget: type[QWidget]) -> Union[str, bool, float, int]:
    if isinstance(widget, QComboBox):
        return widget.currentText()
    elif isinstance(widget, QCheckBox):
        return widget.isChecked()
    elif isinstance(widget, QgsDateTimeEdit):
        return widget.dateTime().toString("yyyy-MM-dd hh:mm:ss")
    elif isinstance(widget, (QgsSpinBox, QgsDoubleSpinBox)):
        return widget.value()
    else:
        return str(widget.text())


def provider_fields(fields: QgsFields) -> QgsFields:
    flds = QgsFields()
    for i in range(fields.count()):
        if fields.fieldOrigin(i) == QgsFields.OriginProvider:
            flds.append(fields.at(i))
    return flds
