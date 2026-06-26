"""Namespace helpers for HWPX XML."""

HWPX_NAMESPACES = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
    "hc": "http://www.hancom.co.kr/hwpml/2011/core",
}


def local_name(tag: str) -> str:
    """Return an XML local name without namespace."""

    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag

