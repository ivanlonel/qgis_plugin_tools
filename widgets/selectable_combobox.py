"""QCombobox with checkbox for selecting multiple items."""

__copyright__ = "Copyright 2019, 3Liz"
__license__ = "GPL version 3"
__email__ = "info@3liz.org"
__revision__ = "$Format:%H$"

from collections.abc import Container
from typing import Optional, cast

from qgis.core import QgsMapLayer, QgsMapLayerType, QgsVectorLayer
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import QAbstractButton, QComboBox, QStyledItemDelegate


class CheckableComboBox:
    """Basic QCombobox with selectable items."""

    def __init__(
        self, combobox: QComboBox, select_all: Optional[QAbstractButton] = None
    ) -> None:
        """Constructor."""
        self.combo = combobox
        self.combo.setEditable(True)
        self.combo.lineEdit().setReadOnly(True)
        self.model = QStandardItemModel(self.combo)
        self.combo.setModel(self.model)
        self.combo.setItemDelegate(QStyledItemDelegate())
        self.model.itemChanged.connect(self.combo_changed)
        self.combo.lineEdit().textChanged.connect(self.text_changed)
        if select_all:
            self.select_all = select_all
            self.select_all.clicked.connect(self.select_all_clicked)

    def select_all_clicked(self) -> None:
        for item in self.model.findItems("*", Qt.MatchFlag.MatchWildcard):
            item.setCheckState(Qt.CheckState.Checked)

    def append_row(self, item: QStandardItem) -> None:
        """Add an item to the combobox."""
        item.setEnabled(True)
        item.setCheckable(True)
        item.setSelectable(False)
        self.model.appendRow(item)

    def combo_changed(self) -> None:
        """Slot when the combo has changed."""
        self.text_changed(None)

    def selected_items(self) -> list:
        return [
            item.data()
            for item in self.model.findItems("*", Qt.MatchFlag.MatchWildcard)
            if item.checkState() == Qt.CheckState.Checked
        ]

    def set_selected_items(self, items: Container) -> None:
        for item in self.model.findItems("*", Qt.MatchFlag.MatchWildcard):
            item.setCheckState(
                Qt.CheckState.Checked
                if item.data() in items
                else Qt.CheckState.Unchecked
            )

    def text_changed(self, text: Optional[str]) -> None:
        """Update the preview with all selected items, separated by a comma."""
        label = ", ".join(self.selected_items())
        if text != label:
            self.combo.setEditText(label)


class CheckableFieldComboBox(CheckableComboBox):
    def __init__(
        self, combobox: QComboBox, select_all: Optional[QAbstractButton] = None
    ) -> None:
        self.layer: Optional[QgsVectorLayer] = None
        super().__init__(combobox, select_all)

    def set_layer(self, layer: Optional[QgsMapLayer]) -> None:
        self.model.clear()

        if not layer:
            return
        if layer.type() != QgsMapLayerType.VectorLayer:
            return

        self.layer = cast(QgsVectorLayer, layer)

        for i, field in enumerate(self.layer.fields()):
            alias = field.alias()
            item = QStandardItem(f"{field.name()} ({alias})" if alias else field.name())
            item.setData(field.name())
            item.setIcon(self.layer.fields().iconForField(i))
            self.append_row(item)
