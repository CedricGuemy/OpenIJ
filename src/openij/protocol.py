"""
OpenIJ
------

Construction des commandes XML du protocole Canon IJ.
"""

from datetime import datetime
from uuid import uuid4


IVEC_NAMESPACE = "http://www.canon.com/ns/cmd/2008/07/common/"
VCN_NAMESPACE = "http://www.canon.com/ns/cmd/2008/07/canon/"


def _cdata(value: str) -> str:
    """Protège une chaîne placée dans une section CDATA."""

    return value.replace("]]>", "]]]]><![CDATA[>")


def build_get_status(
    service_type: str = "maintenance",
) -> str:
    """Construit une commande Canon GetStatus."""

    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<cmd xmlns:ivec="{IVEC_NAMESPACE}">'
        "<ivec:contents>"
        "<ivec:operation>GetStatus</ivec:operation>"
        f'<ivec:param_set servicetype="{service_type}">'
        "</ivec:param_set>"
        "</ivec:contents>"
        "</cmd>"
    )


def build_power_on() -> str:
    """Construit la commande Canon PowerOn."""

    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<cmd xmlns:ivec="{IVEC_NAMESPACE}">'
        "<ivec:contents>"
        "<ivec:operation>PowerOn</ivec:operation>"
        '<ivec:param_set servicetype="device">'
        "<ivec:poweronmode>ModeA</ivec:poweronmode>"
        "</ivec:param_set>"
        "</ivec:contents>"
        "</cmd>"
    )


def build_start_job(
    job_id: str,
    username: str,
    computer_name: str,
    job_description: str | None = None,
) -> str:
    """
    Construit StartJob pour une opération de maintenance.
    """

    if job_description is None:
        job_description = str(uuid4()).upper()

    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<cmd xmlns:ivec="{IVEC_NAMESPACE}" '
        f'xmlns:vcn="{VCN_NAMESPACE}">'
        "<ivec:contents>"
        "<ivec:operation>StartJob</ivec:operation>"
        '<ivec:param_set servicetype="maintenance">'
        f"<ivec:jobID>{job_id}</ivec:jobID>"
        "<ivec:bidi>1</ivec:bidi>"
        f"<ivec:username><![CDATA[{_cdata(username)}]]>"
        "</ivec:username>"
        f"<ivec:computername><![CDATA[{_cdata(computer_name)}]]>"
        "</ivec:computername>"
        f"<ivec:job_description><![CDATA[{_cdata(job_description)}]]>"
        "</ivec:job_description>"
        "<vcn:host_environment>windows</vcn:host_environment>"
        "</ivec:param_set>"
        "</ivec:contents>"
        "</cmd>"
    )


def build_start_device_job(job_id: str) -> str:
    """
    Construit StartJob pour une opération de configuration
    de l'imprimante.
    """

    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<cmd xmlns:ivec="{IVEC_NAMESPACE}">'
        "<ivec:contents>"
        "<ivec:operation>StartJob</ivec:operation>"
        '<ivec:param_set servicetype="device">'
        f"<ivec:jobID>{job_id}</ivec:jobID>"
        "<ivec:bidi>1</ivec:bidi>"
        "</ivec:param_set>"
        "</ivec:contents>"
        "</cmd>"
    )


def build_set_job_configuration(
    job_id: str,
    date_time: datetime | None = None,
) -> str:
    """
    Construit SetJobConfiguration pour une opération
    de maintenance.
    """

    if date_time is None:
        date_time = datetime.now()

    canon_date = date_time.strftime("%Y%m%d%H%M%S")

    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<cmd xmlns:ivec="{IVEC_NAMESPACE}">'
        "<ivec:contents>"
        "<ivec:operation>SetJobConfiguration</ivec:operation>"
        '<ivec:param_set servicetype="maintenance">'
        f"<ivec:jobID>{job_id}</ivec:jobID>"
        f"<ivec:datetime>{canon_date}</ivec:datetime>"
        "</ivec:param_set>"
        "</ivec:contents>"
        "</cmd>"
    )


def build_test_print(
    job_id: str,
    print_type: str,
) -> str:
    """Construit une commande Canon TestPrint."""

    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<cmd xmlns:ivec="{IVEC_NAMESPACE}">'
        "<ivec:contents>"
        "<ivec:operation>TestPrint</ivec:operation>"
        '<ivec:param_set servicetype="maintenance">'
        f"<ivec:jobID>{job_id}</ivec:jobID>"
        f"<ivec:type>{print_type}</ivec:type>"
        "</ivec:param_set>"
        "</ivec:contents>"
        "</cmd>"
    )


def build_set_silent_mode(
    job_id: str,
    enabled: bool,
    date_time: datetime | None = None,
) -> str:
    """
    Construit SetConfiguration pour activer ou désactiver
    le mode silencieux.

    enabled=True  -> ON
    enabled=False -> OFF
    """

    if date_time is None:
        date_time = datetime.now()

    canon_date = date_time.strftime("%Y%m%d%H%M%S")
    mode = "ON" if enabled else "OFF"

    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<cmd xmlns:ivec="{IVEC_NAMESPACE}">'
        "<ivec:contents>"
        "<ivec:operation>SetConfiguration</ivec:operation>"
        '<ivec:param_set servicetype="device">'
        f"<ivec:jobID>{job_id}</ivec:jobID>"
        f"<ivec:datetime>{canon_date}</ivec:datetime>"
        "<ivec:silentmode>"
        f"<ivec:mode>{mode}</ivec:mode>"
        "</ivec:silentmode>"
        "</ivec:param_set>"
        "</ivec:contents>"
        "</cmd>"
    )


def build_end_job(
    job_id: str,
    service_type: str = "maintenance",
) -> str:
    """Construit la commande Canon EndJob."""

    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<cmd xmlns:ivec="{IVEC_NAMESPACE}">'
        "<ivec:contents>"
        "<ivec:operation>EndJob</ivec:operation>"
        f'<ivec:param_set servicetype="{service_type}">'
        f"<ivec:jobID>{job_id}</ivec:jobID>"
        "</ivec:param_set>"
        "</ivec:contents>"
        "</cmd>"
    )