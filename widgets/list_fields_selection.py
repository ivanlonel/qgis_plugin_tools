"""QListWidget with fields selection."""

__copyright__ = "Copyright 2019, 3Liz"
__license__ = "GPL version 3"
__email__ = "info@3liz.org"
__revision__ = "$Format:%H$"

from collections.abc import Container
from typing import Optional

from qgis.core import QgsField, QgsVectorLayer
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QAbstractItemView, QListWidget, QListWidgetItem, QWidget


class ListFieldsSelection(QListWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.layer: Optional[QgsVectorLayer] = None

    def set_layer(self, layer: QgsVectorLayer) -> None:
        self.layer = layer

        self.clear()

        for field in self.layer.fields():
            cell = QListWidgetItem()
            alias = field.alias()
            cell.setText(f"{field.name()} ({alias})" if alias else field.name())
            cell.setData(Qt.ItemDataRole.UserRole, field.name())
            index = layer.fields().indexFromName(field.name())
            if index >= 0:
                cell.setIcon(self.layer.fields().iconForField(index))
            self.addItem(cell)

    def set_selection(self, fields: Container[QgsField]) -> None:
        for i in range(self.count()):
            item = self.item(i)
            item.setSelected(item.data(Qt.ItemDataRole.UserRole) in fields)

    def selection(self) -> list:
        selection = []
        for i in range(self.count()):
            item = self.item(i)
            if item.isSelected():
                selection.append(item.data(Qt.ItemDataRole.UserRole))
        return selection
