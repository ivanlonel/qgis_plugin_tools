__copyright__ = "Copyright 2020-2021, Gispo Ltd"
__license__ = "GPL version 3"
__email__ = "info@gispo.fi"
__revision__ = "$Format:%H$"

import logging
from typing import Optional

from qgis.core import QgsProcessingFeedback

LOGGER = logging.getLogger(__name__)


class LoggerProcessingFeedBack(QgsProcessingFeedback):
    def __init__(self, use_logger: bool = False) -> None:
        super().__init__()
        self._last: Optional[str] = None
        self.use_logger: bool = use_logger
        self.last_progress_text: Optional[str] = None
        self.last_push_info: Optional[str] = None
        self.last_command_info: Optional[str] = None
        self.last_debug_info: Optional[str] = None
        self.last_console_info: Optional[str] = None
        self.last_report_error: Optional[str] = None

    @property
    def last(self) -> Optional[str]:
        return self._last

    @last.setter
    def last(self, text: str) -> None:
        self._last = text

    def setProgressText(self, text: str) -> None:  # noqa: N802
        self._last = text
        self.last_progress_text = text
        if self.use_logger:
            LOGGER.info(text)

    def pushInfo(self, text: str) -> None:  # noqa: N802
        self._last = text
        self.last_push_info = text
        if self.use_logger:
            LOGGER.info(text)

    def pushCommandInfo(self, text: str) -> None:  # noqa: N802
        self._last = text
        self.last_command_info = text
        if self.use_logger:
            LOGGER.info(text)

    def pushDebugInfo(self, text: str) -> None:  # noqa: N802
        self._last = text
        self.last_debug_info = text
        if self.use_logger:
            LOGGER.warning(text)

    def pushConsoleInfo(self, text: str) -> None:  # noqa: N802
        self._last = text
        self.last_console_info = text
        if self.use_logger:
            LOGGER.info(text)

    def reportError(  # noqa: N802
        self, text: str, fatalError: bool = False  # noqa: N803
    ) -> None:
        self._last = text
        self.last_report_error = text
        if self.use_logger:
            LOGGER.exception(text)
