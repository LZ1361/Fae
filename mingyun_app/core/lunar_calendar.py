from __future__ import annotations

from datetime import date, timedelta


BASE_SOLAR_DATE = date(1900, 1, 31)
MIN_YEAR = 1900

# Common Chinese lunar calendar encoding for 1900-2050.
# Low 4 bits: leap month. Month bits: 1 = 30 days, 0 = 29 days.
LUNAR_INFO = [
    0x04BD8, 0x04AE0, 0x0A570, 0x054D5, 0x0D260, 0x0D950, 0x16554, 0x056A0, 0x09AD0, 0x055D2,
    0x04AE0, 0x0A5B6, 0x0A4D0, 0x0D250, 0x1D255, 0x0B540, 0x0D6A0, 0x0ADA2, 0x095B0, 0x14977,
    0x04970, 0x0A4B0, 0x0B4B5, 0x06A50, 0x06D40, 0x1AB54, 0x02B60, 0x09570, 0x052F2, 0x04970,
    0x06566, 0x0D4A0, 0x0EA50, 0x06E95, 0x05AD0, 0x02B60, 0x186E3, 0x092E0, 0x1C8D7, 0x0C950,
    0x0D4A0, 0x1D8A6, 0x0B550, 0x056A0, 0x1A5B4, 0x025D0, 0x092D0, 0x0D2B2, 0x0A950, 0x0B557,
    0x06CA0, 0x0B550, 0x15355, 0x04DA0, 0x0A5B0, 0x14573, 0x052B0, 0x0A9A8, 0x0E950, 0x06AA0,
    0x0AEA6, 0x0AB50, 0x04B60, 0x0AAE4, 0x0A570, 0x05260, 0x0F263, 0x0D950, 0x05B57, 0x056A0,
    0x096D0, 0x04DD5, 0x04AD0, 0x0A4D0, 0x0D4D4, 0x0D250, 0x0D558, 0x0B540, 0x0B5A0, 0x195A6,
    0x095B0, 0x049B0, 0x0A974, 0x0A4B0, 0x0B27A, 0x06A50, 0x06D40, 0x0AF46, 0x0AB60, 0x09570,
    0x04AF5, 0x04970, 0x064B0, 0x074A3, 0x0EA50, 0x06B58, 0x05AC0, 0x0AB60, 0x096D5, 0x092E0,
    0x0C960, 0x0D954, 0x0D4A0, 0x0DA50, 0x07552, 0x056A0, 0x0ABB7, 0x025D0, 0x092D0, 0x0CAB5,
    0x0A950, 0x0B4A0, 0x0BAA4, 0x0AD50, 0x055D9, 0x04BA0, 0x0A5B0, 0x15176, 0x052B0, 0x0A930,
    0x07954, 0x06AA0, 0x0AD50, 0x05B52, 0x04B60, 0x0A6E6, 0x0A4E0, 0x0D260, 0x0EA65, 0x0D530,
    0x05AA0, 0x076A3, 0x096D0, 0x04BD7, 0x04AD0, 0x0A4D0, 0x1D0B6, 0x0D250, 0x0D520, 0x0DD45,
    0x0B5A0, 0x056D0, 0x055B2, 0x049B0, 0x0A577, 0x0A4B0, 0x0AA50, 0x1B255, 0x06D20, 0x0ADA0,
    0x14B63,
]
MAX_YEAR = MIN_YEAR + len(LUNAR_INFO) - 1


def lunar_to_solar(year: int, month: int, day: int, is_leap: bool = False) -> date:
    _validate_year(year)
    if not 1 <= month <= 12:
        raise ValueError("lunar month must be between 1 and 12")

    leap_month = get_leap_month(year)
    if is_leap and leap_month != month:
        raise ValueError(f"lunar year {year} does not have leap month {month}")

    max_day = get_leap_month_days(year) if is_leap else get_month_days(year, month)
    if not 1 <= day <= max_day:
        raise ValueError(f"lunar day must be between 1 and {max_day}")

    offset = 0
    for current_year in range(MIN_YEAR, year):
        offset += get_year_days(current_year)

    for current_month in range(1, month):
        offset += get_month_days(year, current_month)
        if leap_month == current_month:
            offset += get_leap_month_days(year)

    if is_leap:
        offset += get_month_days(year, month)

    return BASE_SOLAR_DATE + timedelta(days=offset + day - 1)


def get_year_days(year: int) -> int:
    _validate_year(year)
    info = LUNAR_INFO[year - MIN_YEAR]
    days = 348
    bit = 0x8000
    while bit > 0x8:
        if info & bit:
            days += 1
        bit >>= 1
    return days + get_leap_month_days(year)


def get_leap_month(year: int) -> int:
    _validate_year(year)
    return LUNAR_INFO[year - MIN_YEAR] & 0xF


def get_leap_month_days(year: int) -> int:
    leap_month = get_leap_month(year)
    if not leap_month:
        return 0
    return 30 if (LUNAR_INFO[year - MIN_YEAR] & 0x10000) else 29


def get_month_days(year: int, month: int) -> int:
    _validate_year(year)
    if not 1 <= month <= 12:
        raise ValueError("lunar month must be between 1 and 12")
    return 30 if (LUNAR_INFO[year - MIN_YEAR] & (0x10000 >> month)) else 29


def _validate_year(year: int) -> None:
    if year < MIN_YEAR or year > MAX_YEAR:
        raise ValueError(f"lunar year must be between {MIN_YEAR} and {MAX_YEAR}")
