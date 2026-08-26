import re

from fastapi import HTTPException, status


_DIGITS = re.compile(r"\D+")


def format_valid_phone_number(country_code: str | None, mobile: str | None) -> str:
    if not mobile:
        return ""

    digits = _DIGITS.sub("", mobile)
    if not digits:
        return ""

    cc = _DIGITS.sub("", country_code or "")
    if cc and not cc.startswith("+"):
        cc = f"+{cc}"

    normalized = f"{cc}{digits}" if cc else digits
    if len(digits) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"message": "Invalid mobile number"})

    return normalized

