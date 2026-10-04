"""Bounded NYSE equity calendar, verified against ICE's 2023–25 notices."""
from datetime import date, timedelta
from bisect import bisect_left, bisect_right

SOURCES = [
 'https://ir.theice.com/press/news-details/2022/NYSE-Group-Announces-2023-2024-and-2025-Holiday-and-Early-Closings-Calendar/default.aspx',
 'https://ir.theice.com/press/news-details/2024/The-New-York-Stock-Exchange-Will-Close-Markets-on-January-9-to-Honor-the-Passing-of-Former-President-Jimmy-Carter-on-National-Day-of-Mourning/default.aspx',
]
HOLIDAYS = set('''2023-01-02 2023-01-16 2023-02-20 2023-04-07 2023-05-29 2023-06-19 2023-07-04 2023-09-04 2023-11-23 2023-12-25
2024-01-01 2024-01-15 2024-02-19 2024-03-29 2024-05-27 2024-06-19 2024-07-04 2024-09-02 2024-11-28 2024-12-25
2025-01-01 2025-01-09 2025-01-20 2025-02-17 2025-04-18 2025-05-26 2025-06-19 2025-07-04 2025-09-01 2025-11-27 2025-12-25'''.split())
EARLY_CLOSES = set('2023-07-03 2023-11-24 2024-07-03 2024-11-29 2024-12-24 2025-07-03 2025-11-28 2025-12-24'.split())
SESSIONS = [str(date(2023,1,1)+timedelta(days=i)) for i in range(1096)
            if (date(2023,1,1)+timedelta(days=i)).weekday()<5
            and str(date(2023,1,1)+timedelta(days=i)) not in HOLIDAYS]
START_INDEX = bisect_left(SESSIONS,'2023-04-03')
ACQUISITION_DATES = SESSIONS[START_INDEX-20:]

def session_index(event_date, timing):
    """Never resolve beyond 2025; return None for outside development D."""
    if timing not in ('bmo','amc'):
        return None
    i = (bisect_left if timing=='bmo' else bisect_right)(SESSIONS,event_date)
    if i >= len(SESSIONS) or SESSIONS[i] < '2023-04-03':
        return None
    return i
