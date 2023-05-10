"""Base class algorithm."""

__copyright__ = "Copyright 2020, 3Liz"
__license__ = "GPL version 3"
__email__ = "info@3liz.org"
__revision__ = "$Format:%H$"

from os.path import isfile
from typing import cast

from qgis.core import QgsProcessingAlgorithm
from qgis.PyQt.QtGui import QIcon

from .resources import resources_path


class BaseProcessingAlgorithm(QgsProcessingAlgorithm):
    def createInstance(self) -> "BaseProcessingAlgorithm":  # noqa: N802
        return type(self)()

    def flags(self) -> QgsProcessingAlgorithm.Flags:
        return cast(
            QgsProcessingAlgorithm.Flags,
            super().flags() | QgsProcessingAlgorithm.Flag.FlagHideFromModeler,
        )

    def icon(self) -> QIcon:
        icon = resources_path("icons", "icon.png")
        return QIcon(icon) if isfile(icon) else super().icon()

    def shortHelpString(self) -> str:  # noqa: N802
        raise NotImplementedError
