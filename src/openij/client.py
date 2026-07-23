"""
OpenIJ
------

Client réseau pour le protocole Canon IJ.
"""

import getpass
import platform
import socket
import time
import xml.etree.ElementTree as ET

from dataclasses import dataclass
from typing import BinaryIO

from openij.protocol import (
    IVEC_NAMESPACE,
    build_end_job,
    build_get_status,
    build_power_on,
    build_set_job_configuration,
    build_set_silent_mode,
    build_start_device_job,
    build_start_job,
    build_test_print,
)


@dataclass
class CanonResponse:
    """Réponse retournée par l'imprimante."""

    status_code: int
    text: str


@dataclass
class MaintenanceJobResult:
    """Résultat d'un travail de maintenance Canon."""

    job_id: str
    operation: str | None
    response: str | None
    response_detail: str | None
    progress: str | None
    status_xml: str


class CanonClient:
    """Client réseau OpenIJ pour les imprimantes Canon compatibles."""

    def __init__(
        self,
        ip_address: str,
        port: int = 80,
        timeout: float = 10.0,
    ):
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout

        self.path = "/canon/ij/command2/port1"

        self.url = (
            f"http://{ip_address}:{port}{self.path}"
            if port != 80
            else f"http://{ip_address}{self.path}"
        )

    @staticmethod
    def _read_exactly(
        reader: BinaryIO,
        length: int,
    ) -> bytes:
        """Lit exactement le nombre d'octets demandé."""

        data = reader.read(length)

        if data is None or len(data) != length:
            received = 0 if data is None else len(data)

            raise ConnectionError(
                "Connexion interrompue pendant la lecture : "
                f"{received}/{length} octets reçus."
            )

        return data

    @staticmethod
    def _read_chunked_body(
        reader: BinaryIO,
    ) -> bytes:
        """Décode un corps HTTP utilisant le mode chunked."""

        body = bytearray()

        while True:
            size_line_bytes = reader.readline()

            if not size_line_bytes:
                raise ConnectionError(
                    "Connexion interrompue pendant la lecture "
                    "de la taille d'un bloc HTTP."
                )

            size_line = size_line_bytes.decode(
                "ascii",
                errors="replace",
            ).strip()

            size_text = size_line.split(";", 1)[0]

            try:
                chunk_size = int(size_text, 16)
            except ValueError as error:
                raise ConnectionError(
                    f"Taille de bloc HTTP invalide : {size_line}"
                ) from error

            if chunk_size == 0:
                while True:
                    trailer = reader.readline()

                    if not trailer or trailer in (b"\r\n", b"\n"):
                        break

                break

            chunk = CanonClient._read_exactly(
                reader,
                chunk_size,
            )

            body.extend(chunk)

            ending = CanonClient._read_exactly(
                reader,
                2,
            )

            if ending != b"\r\n":
                raise ConnectionError(
                    "Fin de bloc HTTP chunked invalide."
                )

        return bytes(body)

    @staticmethod
    def _read_http_response(
        reader: BinaryIO,
    ) -> tuple[int, dict[str, str], bytes]:
        """Lit une réponse HTTP complète."""

        status_line_bytes = reader.readline()

        if not status_line_bytes:
            raise ConnectionError(
                "L'imprimante n'a retourné aucune réponse HTTP."
            )

        status_line = status_line_bytes.decode(
            "iso-8859-1",
            errors="replace",
        ).strip()

        parts = status_line.split(" ", 2)

        if len(parts) < 2:
            raise ConnectionError(
                f"Ligne de statut HTTP invalide : {status_line}"
            )

        try:
            status_code = int(parts[1])
        except ValueError as error:
            raise ConnectionError(
                f"Code HTTP invalide : {status_line}"
            ) from error

        headers: dict[str, str] = {}

        while True:
            line_bytes = reader.readline()

            if not line_bytes:
                raise ConnectionError(
                    "Connexion interrompue pendant la lecture "
                    "des en-têtes HTTP."
                )

            if line_bytes in (b"\r\n", b"\n"):
                break

            line = line_bytes.decode(
                "iso-8859-1",
                errors="replace",
            ).rstrip("\r\n")

            if ":" not in line:
                continue

            name, value = line.split(":", 1)

            headers[name.strip().lower()] = value.strip()

        body = b""

        transfer_encoding = headers.get(
            "transfer-encoding",
            "",
        ).lower()

        if "chunked" in transfer_encoding:
            body = CanonClient._read_chunked_body(reader)

        elif "content-length" in headers:
            try:
                content_length = int(
                    headers["content-length"]
                )
            except ValueError as error:
                raise ConnectionError(
                    "Content-Length HTTP invalide."
                ) from error

            if content_length > 0:
                body = CanonClient._read_exactly(
                    reader,
                    content_length,
                )

        return status_code, headers, body

    def _build_post_request(
        self,
        xml_data: bytes,
    ) -> bytes:
        """Construit la requête HTTP POST Canon."""

        headers = (
            f"POST {self.path} HTTP/1.1\r\n"
            f"Host: {self.ip_address}\r\n"
            "Connection: Keep-Alive\r\n"
            "Content-Type: application/octet-stream\r\n"
            f"Content-Length: {len(xml_data)}\r\n"
            "X-CHMP-Version: 1.3.0\r\n"
            "\r\n"
        )

        return headers.encode("ascii") + xml_data

    def _build_get_request(self) -> bytes:
        """Construit la requête HTTP GET Canon."""

        request = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.ip_address}\r\n"
            "Connection: Keep-Alive\r\n"
            "X-CHMP-Version: 1.3.0\r\n"
            "\r\n"
        )

        return request.encode("ascii")

    def _send_command_on_connection(
        self,
        sock: socket.socket,
        reader: BinaryIO,
        xml: str,
    ) -> CanonResponse:
        """
        Envoie une commande sur une connexion TCP déjà ouverte.

        Le POST et le GET associés utilisent la même connexion.
        """

        xml_data = xml.encode("utf-8")

        sock.sendall(
            self._build_post_request(xml_data)
        )

        (
            post_status,
            _post_headers,
            _post_body,
        ) = self._read_http_response(reader)

        if post_status != 200:
            raise ConnectionError(
                f"Le POST Canon a retourné HTTP {post_status}."
            )

        sock.sendall(
            self._build_get_request()
        )

        (
            get_status,
            _get_headers,
            get_body,
        ) = self._read_http_response(reader)

        if get_status != 200:
            raise ConnectionError(
                f"Le GET Canon a retourné HTTP {get_status}."
            )

        if not get_body:
            raise ConnectionError(
                "Canon a retourné une réponse HTTP vide."
            )

        xml_response = get_body.decode(
            "utf-8",
            errors="replace",
        ).strip()

        if not xml_response.startswith("<?xml"):
            raise ConnectionError(
                "La réponse Canon ne contient pas "
                "un document XML reconnu."
            )

        return CanonResponse(
            status_code=get_status,
            text=xml_response,
        )

    def send_command(self, xml: str) -> CanonResponse:
        """Envoie une commande Canon isolée."""

        try:
            with socket.create_connection(
                (self.ip_address, self.port),
                timeout=self.timeout,
            ) as sock:

                sock.settimeout(self.timeout)

                with sock.makefile("rb") as reader:
                    return self._send_command_on_connection(
                        sock,
                        reader,
                        xml,
                    )

        except socket.timeout as error:
            raise ConnectionError(
                "Délai de communication dépassé."
            ) from error

        except OSError as error:
            raise ConnectionError(
                f"Erreur réseau : {error}"
            ) from error

    @staticmethod
    def _get_xml_value(
        xml_text: str,
        tag_name: str,
    ) -> str | None:
        """Extrait la valeur d'une balise IVEC."""

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as error:
            raise ConnectionError(
                "La réponse Canon contient un XML invalide."
            ) from error

        namespaces = {
            "ivec": IVEC_NAMESPACE,
        }

        element = root.find(
            f".//ivec:{tag_name}",
            namespaces,
        )

        if element is None or element.text is None:
            return None

        value = element.text.strip()

        return value or None

    @classmethod
    def _check_canon_response(
        cls,
        response: CanonResponse,
        expected_operation: str,
    ) -> None:
        """Vérifie que Canon a répondu OK."""

        operation = cls._get_xml_value(
            response.text,
            "operation",
        )

        canon_result = cls._get_xml_value(
            response.text,
            "response",
        )

        response_detail = cls._get_xml_value(
            response.text,
            "response_detail",
        )

        if operation != expected_operation:
            raise ConnectionError(
                "Réponse Canon inattendue : "
                f"{operation!r} au lieu de "
                f"{expected_operation!r}."
            )

        if canon_result != "OK":
            detail = response_detail or "aucun détail"

            raise ConnectionError(
                f"Canon a refusé {expected_operation} : "
                f"{canon_result or 'réponse inconnue'} "
                f"({detail})."
            )

    def get_status(
        self,
        service_type: str = "maintenance",
    ) -> CanonResponse:
        """Interroge l'état de l'imprimante."""

        return self.send_command(
            build_get_status(service_type)
        )

    def power_on(self) -> CanonResponse:
        """Réveille l'imprimante."""

        response = self.send_command(
            build_power_on()
        )

        self._check_canon_response(
            response,
            "PowerOnResponse",
        )

        return response

    def ensure_awake(
        self,
        attempts: int = 20,
        delay: float = 1.0,
    ) -> None:
        """Réveille l'imprimante lorsqu'elle est suspendue."""

        status = self.get_status(
            service_type="print"
        )

        canon_response = self._get_xml_value(
            status.text,
            "response",
        )

        response_detail = self._get_xml_value(
            status.text,
            "response_detail",
        )

        if canon_response == "OK":
            return

        if response_detail != "Suspended":
            raise ConnectionError(
                "L'imprimante n'est pas disponible : "
                f"{canon_response or 'réponse inconnue'} "
                f"({response_detail or 'aucun détail'})."
            )

        self.power_on()

        last_response = canon_response
        last_detail = response_detail

        for _ in range(attempts):
            time.sleep(delay)

            status = self.get_status(
                service_type="print"
            )

            last_response = self._get_xml_value(
                status.text,
                "response",
            )

            last_detail = self._get_xml_value(
                status.text,
                "response_detail",
            )

            if last_response == "OK":
                return

        raise ConnectionError(
            "L'imprimante ne s'est pas réveillée "
            "dans le délai prévu : "
            f"{last_response or 'réponse inconnue'} "
            f"({last_detail or 'aucun détail'})."
        )

    def set_quiet_mode(
        self,
        enabled: bool,
        job_id: str = "00000002",
    ) -> CanonResponse:
        """
        Active ou désactive le mode silencieux.

        Toutes les commandes utilisent la même connexion TCP :

        1. StartJob / device
        2. SetConfiguration / silentmode
        3. EndJob / device
        """

        self.ensure_awake()

        configuration_response: CanonResponse | None = None
        job_started = False

        try:
            with socket.create_connection(
                (self.ip_address, self.port),
                timeout=self.timeout,
            ) as sock:

                sock.settimeout(self.timeout)

                with sock.makefile("rb") as reader:
                    try:
                        start_response = (
                            self._send_command_on_connection(
                                sock,
                                reader,
                                build_start_device_job(job_id),
                            )
                        )

                        self._check_canon_response(
                            start_response,
                            "StartJobResponse",
                        )

                        job_started = True

                        configuration_response = (
                            self._send_command_on_connection(
                                sock,
                                reader,
                                build_set_silent_mode(
                                    job_id=job_id,
                                    enabled=enabled,
                                ),
                            )
                        )

                        self._check_canon_response(
                            configuration_response,
                            "SetConfigurationResponse",
                        )

                    except Exception:
                        if job_started:
                            try:
                                self._send_command_on_connection(
                                    sock,
                                    reader,
                                    build_end_job(
                                        job_id,
                                        service_type="device",
                                    ),
                                )
                            except Exception:
                                pass

                        raise

                    else:
                        end_response = (
                            self._send_command_on_connection(
                                sock,
                                reader,
                                build_end_job(
                                    job_id,
                                    service_type="device",
                                ),
                            )
                        )

                        self._check_canon_response(
                            end_response,
                            "EndJobResponse",
                        )

        except socket.timeout as error:
            raise ConnectionError(
                "Délai de communication dépassé "
                "pendant la configuration."
            ) from error

        except OSError as error:
            raise ConnectionError(
                "Erreur réseau pendant la configuration : "
                f"{error}"
            ) from error

        if configuration_response is None:
            raise ConnectionError(
                "La configuration du mode silencieux "
                "n'a retourné aucune réponse."
            )

        return configuration_response

    def automatic_head_alignment(
        self,
        job_id: str = "00000002",
        username: str | None = None,
        computer_name: str | None = None,
    ) -> MaintenanceJobResult:
        """Lance l'alignement automatique de la tête."""

        if username is None:
            username = getpass.getuser()

        if computer_name is None:
            computer_name = platform.node()

        self.ensure_awake()

        status_response: CanonResponse | None = None
        job_started = False

        try:
            with socket.create_connection(
                (self.ip_address, self.port),
                timeout=self.timeout,
            ) as sock:

                sock.settimeout(self.timeout)

                with sock.makefile("rb") as reader:
                    try:
                        start_response = (
                            self._send_command_on_connection(
                                sock,
                                reader,
                                build_start_job(
                                    job_id=job_id,
                                    username=username,
                                    computer_name=computer_name,
                                ),
                            )
                        )

                        self._check_canon_response(
                            start_response,
                            "StartJobResponse",
                        )

                        job_started = True

                        configuration_response = (
                            self._send_command_on_connection(
                                sock,
                                reader,
                                build_set_job_configuration(
                                    job_id
                                ),
                            )
                        )

                        self._check_canon_response(
                            configuration_response,
                            "SetJobConfigurationResponse",
                        )

                        test_print_response = (
                            self._send_command_on_connection(
                                sock,
                                reader,
                                build_test_print(
                                    job_id=job_id,
                                    print_type=(
                                        "half_auto_registration"
                                    ),
                                ),
                            )
                        )

                        self._check_canon_response(
                            test_print_response,
                            "TestPrintResponse",
                        )

                        status_response = (
                            self._send_command_on_connection(
                                sock,
                                reader,
                                build_get_status(
                                    "maintenance"
                                ),
                            )
                        )

                        self._check_canon_response(
                            status_response,
                            "GetStatusResponse",
                        )

                    except Exception:
                        if job_started:
                            try:
                                self._send_command_on_connection(
                                    sock,
                                    reader,
                                    build_end_job(job_id),
                                )
                            except Exception:
                                pass

                        raise

                    else:
                        end_response = (
                            self._send_command_on_connection(
                                sock,
                                reader,
                                build_end_job(job_id),
                            )
                        )

                        self._check_canon_response(
                            end_response,
                            "EndJobResponse",
                        )

        except socket.timeout as error:
            raise ConnectionError(
                "Délai de communication dépassé "
                "pendant l'alignement."
            ) from error

        except OSError as error:
            raise ConnectionError(
                f"Erreur réseau pendant l'alignement : {error}"
            ) from error

        if status_response is None:
            raise ConnectionError(
                "Impossible de récupérer l'état "
                "de l'alignement."
            )

        return MaintenanceJobResult(
            job_id=job_id,
            operation=self._get_xml_value(
                status_response.text,
                "maintenance_operation",
            ),
            response=self._get_xml_value(
                status_response.text,
                "response",
            ),
            response_detail=self._get_xml_value(
                status_response.text,
                "response_detail",
            ),
            progress=self._get_xml_value(
                status_response.text,
                "jobprogress",
            ),
            status_xml=status_response.text,
        )