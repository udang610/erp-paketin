import re


def clean_city_name(city):
    if not city:
        return ""
    value = str(city).strip()
    if " - " in value:
        prefix, value = value.split(" - ", 1)
        if len(prefix.strip()) <= 4:
            value = value.strip()
    if "," in value:
        value = value.split(",")[-1].strip()
    hub_match = re.search(r"(?i)(?:kota|kabupaten)\s+(.+)$", value)
    if value.lower().startswith("di hub ") and hub_match:
        value = hub_match.group(0)
    return value.strip()


def city_display_name(city):
    value = clean_city_name(city)
    value = re.sub(r"(?i)^kota\s+", "", value).strip()
    return re.sub(r"(?i)^kabupaten\s+", "Kab. ", value).strip().title()


def coverage_city_label(coverage):
    city = city_display_name(coverage.city)
    tlc = (coverage.tlc or "").upper()
    return f"{tlc} - {city}" if tlc else city


def coverage_district_label(coverage):
    tlc = (coverage.tlc or "").upper()
    code = f"{tlc}{coverage.id}" if tlc else str(coverage.id)
    return f"{code} - {coverage.district}" if code else coverage.district


def clean_branch_label(branch_obj):
    if not branch_obj:
        return "-"
    name = getattr(branch_obj, 'name', str(branch_obj))
    code = getattr(branch_obj, 'code', None)
    clean_name = re.sub(r'(?i)\b(cabang|kota|kabupaten|kab\.)\b\s*', '', name).strip()
    return f"{clean_name} ({code})" if code else clean_name

