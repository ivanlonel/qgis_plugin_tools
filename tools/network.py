import json
import logging
import re
import shutil
from pathlib import Path
from typing import Literal, NamedTuple, Optional, Union
from urllib.parse import urlencode
from uuid import uuid4

from qgis.core import Qgis, QgsBlockingNetworkRequest, QgsNetworkReplyContent
from qgis.PyQt.QtCore import QByteArray, QSettings, QUrl
from qgis.PyQt.QtNetwork import QNetworkReply, QNetworkRequest

from ..tools.exceptions import QgsPluginNetworkException
from ..tools.i18n import tr
from ..tools.resources import plugin_name
from .custom_logging import bar_msg

try:
    import requests
except ImportError:
    REQUESTS_IS_AVAILABLE = False
else:
    REQUESTS_IS_AVAILABLE = True

__copyright__ = "Copyright 2020-2023, Gispo Ltd"
__license__ = "GPL version 3"
__email__ = "info@gispo.fi"
__revision__ = "$Format:%H$"

LOGGER = logging.getLogger(__name__)
ENCODING = "utf-8"
CONTENT_DISPOSITION_HEADER = "Content-Disposition"
CONTENT_DISPOSITION_BYTE_HEADER = QByteArray(
    bytes(CONTENT_DISPOSITION_HEADER, ENCODING)
)


class FileInfo(NamedTuple):
    file_name: str
    content: bytes
    content_type: str


class FileField(NamedTuple):
    field_name: str
    file_info: FileInfo


def fetch(
    url: str,
    encoding: str = ENCODING,
    authcfg_id: str = "",
    params: Optional[dict[str, str]] = None,
) -> str:
    """
    Fetch resource from the internet. Similar to requests.get(url) but is
    recommended way of handling requests in QGIS plugin
    :param url: address of the web resource
    :param encoding: Encoding which will be used to decode the bytes
    :param authcfg_id: authcfg id from QGIS settings, defaults to ''
    :param params: Dictionary to send in the query string
    :return: encoded string of the content
    """
    content, _ = fetch_raw(url, encoding, authcfg_id, params)
    return content.decode(ENCODING)


def post(
    url: str,
    encoding: str = ENCODING,
    authcfg_id: str = "",
    data: Optional[dict[str, str]] = None,
    files: Optional[list[FileField]] = None,
) -> str:
    """
    Post resource. Similar to requests.post(url, data, files) but is
    recommended way of handling requests in QGIS plugin
    :param url: address of the web resource
    :param encoding: Encoding which will be used to decode the bytes
    :param authcfg_id: authcfg id from QGIS settings, defaults to ''
    :param data: Dictionary to send in the request body
    :param files: Files to send multipart-encoded. Same format as requests.
    :return: encoded string of the content
    """
    content, _ = post_raw(url, encoding, authcfg_id, data, files)
    return content.decode(ENCODING)


def fetch_raw(
    url: str,
    encoding: str = ENCODING,
    authcfg_id: str = "",
    params: Optional[dict[str, str]] = None,
) -> tuple[bytes, str]:
    """
    Fetch resource from the internet. Similar to requests.get(url) but is
    recommended way of handling requests in QGIS plugin
    :param url: address of the web resource
    :param encoding: Encoding which will be used to decode the bytes
    :param authcfg_id: authcfg id from QGIS settings, defaults to ''
    :param params: Dictionary to send in the query string
    :return: bytes of the content and default name of the file or empty string
    """
    return request_raw(url, "get", encoding, authcfg_id, params)


def post_raw(
    url: str,
    encoding: str = ENCODING,
    authcfg_id: str = "",
    data: Optional[dict[str, str]] = None,
    files: Optional[list[FileField]] = None,
) -> tuple[bytes, str]:
    """
    Post resource. Similar to requests.post(url, data, files) but is
    recommended way of handling requests in QGIS plugin
    :param url: address of the web resource
    :param encoding: Encoding which will be used to decode the bytes
    :param authcfg_id: authcfg id from QGIS settings, defaults to ''
    :param data: Dictionary to send in the request body
    :param files: Files to send multipart-encoded. Same format as requests.
    :return: bytes of the content and default name of the file or empty string
    """
    return request_raw(url, "post", encoding, authcfg_id, None, data, files)


def request_raw(
    url: str,
    method: Literal["get", "post"] = "get",
    encoding: str = ENCODING,
    authcfg_id: str = "",
    params: Optional[dict[str, str]] = None,
    data: Optional[dict[str, str]] = None,
    files: Optional[list[FileField]] = None,
) -> tuple[bytes, str]:
    """
    Request resource from the internet. Similar to requests.get(url) and
    requests.post(url, data) but is recommended way of handling requests in QGIS plugin
    :param url: address of the web resource
    :param method: method to use, defaults to 'get'
    :param encoding: Encoding which will be used to decode the bytes
    :param authcfg_id: authcfg id from QGIS settings, defaults to ''
    :param params: Dictionary to send in the query string
    :param data: Dictionary to send in the request body
    :param files: Files to send multipart-encoded. Same format as requests.
    :return: bytes of the content and default name of the file or empty string
    """
    if params:
        url += f"?{urlencode(params)}"
    LOGGER.debug(url)
    req = QNetworkRequest(QUrl(url))
    # http://osgeo-org.1560.x6.nabble.com/QGIS-Developer-Do-we-have-a-User-Agent-string-for-QGIS-td5360740.html
    user_agent = QSettings().value("/qgis/networkAndProxy/userAgent", "Mozilla/5.0")
    user_agent += " " if user_agent else ""
    # noinspection PyUnresolvedReferences
    user_agent += f"QGIS/{Qgis.QGIS_VERSION_INT} {plugin_name()}"
    # https://www.riverbankcomputing.com/pipermail/pyqt/2016-May/037514.html
    req.setRawHeader(b"User-Agent", bytes(user_agent, encoding))
    request_blocking = QgsBlockingNetworkRequest()
    if authcfg_id:
        request_blocking.setAuthCfg(authcfg_id)
    # QNetworkRequest *only* supports get and post. No idea why.
    if method == "get":
        _ = request_blocking.get(req)
    elif method == "post":
        if data:
            # Support JSON
            byte_data = bytes(json.dumps(data), encoding)
            req.setRawHeader(
                b"Content-Type",
                bytes(f"application/json; charset={encoding}", encoding),
            )
        elif files:
            # Support multipart binary. Generate boundary like
            # https://github.com/requests/toolbelt/blob/master/requests_toolbelt/multipart/encoder.py
            boundary = uuid4().hex
            byte_boundary = bytes(f"\r\n--{boundary}\r\n", encoding)

            # each file may have different content type, name and filename
            byte_data = b""
            for file_field in files:
                file_info = file_field[1]
                content_disposition_form_data = (
                    "Content-Disposition: form-data;"
                    f' name="{file_field[0]}";'
                    f' filename="{file_info[0]}"\r\n'
                )
                byte_data += (
                    byte_boundary
                    + bytes(content_disposition_form_data, encoding)
                    + bytes(f"Content-Type: {file_info[2]}\r\n\r\n", encoding)
                    + file_info[1]
                )
            byte_data += bytes(f"\r\n--{boundary}--\r\n", encoding)
            req.setRawHeader(
                b"Content-Type",
                bytes(f"multipart/form-data; boundary={boundary}", encoding),
            )
        else:
            byte_data = b""
        _ = request_blocking.post(req, byte_data)
    else:
        raise ValueError(f"Request method {method} not supported.")
    reply: QgsNetworkReplyContent = request_blocking.reply()
    reply_error = reply.error()
    if reply_error != QNetworkReply.NetworkError.NoError:
        # Error content will be empty in older QGIS versions:
        # https://github.com/qgis/QGIS/issues/42442

        # bar_msg will just show a generic Qt error string.
        raise QgsPluginNetworkException(
            message=(
                bytes(reply.content()).decode("utf-8")
                if bytes(reply.content())
                else None
            ),
            error=reply_error,
            bar_msg=bar_msg(reply.errorString()),
        )

    # https://stackoverflow.com/a/39103880/10068922
    default_name = ""
    if reply.hasRawHeader(CONTENT_DISPOSITION_BYTE_HEADER):
        header: QByteArray = reply.rawHeader(CONTENT_DISPOSITION_BYTE_HEADER)
        default_name = bytes(header).decode(encoding).split("filename=")[1]
        if default_name[0] in ['"', "'"]:
            default_name = default_name[1:-1]

    return bytes(reply.content()), default_name


def download_to_file(
    url: str,
    output_dir: Path,
    output_name: Optional[str] = None,
    use_requests_if_available: bool = True,
    encoding: str = ENCODING,
    timeout: Optional[Union[float, tuple[float, float]]] = None,
) -> Path:
    """
    Downloads a binary file to the file efficiently
    :param url: Url of the file
    :param output_dir: Path to the output directory
    :param output_name: If given, use this as file name. Otherwise reads file name from
    Content-Disposition header or uses the url
    :param use_requests_if_available: Use Python package requests
    if it is available in the environment
    :param encoding: Encoding which will be used to decode the bytes
    :param timeout: How many seconds to wait for the server to send data before giving
    up, as a float, or a (connect timeout, read timeout) tuple.
    :return: Path to the file
    """

    def get_output(default_filename: str) -> Path:
        if output_name is None:
            if default_filename != "":
                out_name = default_filename
            else:
                out_name = url.replace("http://", "").replace("https://", "")
                if len(out_name.split("/")[-1]) > 2:
                    out_name = out_name.split("/")[-1]
        else:
            out_name = output_name
        return Path(output_dir, out_name)

    output = Path()

    if use_requests_if_available and REQUESTS_IS_AVAILABLE:
        # https://stackoverflow.com/a/39217788/10068922

        try:
            with requests.get(url, stream=True, timeout=timeout) as r:
                try:
                    r.raise_for_status()
                except Exception as e:
                    raise QgsPluginNetworkException(
                        tr("Request failed with status code {}", r.status_code),
                        bar_msg=bar_msg(r.text),
                    ) from e
                default_filenames = re.findall(
                    "filename=(.+)", r.headers.get(CONTENT_DISPOSITION_HEADER, "")
                )
                default_filename = default_filenames[0] if default_filenames else ""
                output = get_output(default_filename)
                with open(output, "wb") as f:
                    shutil.copyfileobj(r.raw, f)
        except requests.exceptions.RequestException as e:
            raise QgsPluginNetworkException(
                tr("Request failed"), bar_msg=bar_msg(e)
            ) from e
    else:
        # Using simple fetch_raw
        content, default_filename = fetch_raw(url, encoding)
        output = get_output(default_filename)
        with open(output, "wb") as f:
            f.write(content)
    return output
