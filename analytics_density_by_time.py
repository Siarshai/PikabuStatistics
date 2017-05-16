from enum import Enum
import os
import datetime
from drawing import draw_rating_hourly, draw_rating_daily, draw_rating_monthly
from utils import extract_rating_by_time, discretize, clean_folders
import numpy as np



RESULT_FOLDER = "posts_density_by_time"


class _TimestampFormat(Enum):
    HOURLY = 1,
    HOURLY_WEEKDAY = 2,
    DAILY = 3,
    MONTHLY = 4

def _roll_timestamps(timestamps, format):
    if format not in [_TimestampFormat.DAILY, _TimestampFormat.HOURLY, _TimestampFormat.HOURLY_WEEKDAY, _TimestampFormat.MONTHLY]:
        raise RuntimeError("Invalid rolling format")
    rolled_timestamps = []
    for ts_numeric in timestamps:
        ts = datetime.datetime.fromtimestamp(ts_numeric)
        day_of_week = ts.weekday()
        year, month, day, hour, minute, second = ts.strftime('%Y %m %d %H %M %S').split()
        year, month, day, hour, minute, second = float(year), float(month), float(day), float(hour), float(minute), float(second)
        if format == _TimestampFormat.HOURLY:
            rolled_timestamps.append(60*60*hour + 60*minute + second)
        elif format == _TimestampFormat.HOURLY_WEEKDAY:
            if day_of_week in range(0, 5):
                rolled_timestamps.append(60*60*hour + 60*minute + second)
        elif format == _TimestampFormat.DAILY:
            rolled_timestamps.append(24*60*60*day_of_week + 60*60*hour + 60*minute + second)
        elif format == _TimestampFormat.MONTHLY:
            rolled_timestamps.append(24*60*60*(day-1) + 60*60*hour + 60*minute + second)
    return np.asarray(rolled_timestamps)


def analyze_density_by_time(data):

    print("Analyze density by time")
    clean_folders([RESULT_FOLDER])

    T, R = extract_rating_by_time(data, lambda x: True)

    print("Analyze density by time: hourly for weekdays")
    rolled_timestamps = _roll_timestamps(T, _TimestampFormat.HOURLY_WEEKDAY)
    N_rolled, R_rolled = discretize(X=rolled_timestamps, Y=R, bins=2*24, normalize=False)
    corresponding_time_ticks = np.arange(0, 24*60*60, 30*60)
    path_to_save = os.path.join(RESULT_FOLDER, "hourly_weekday")
    draw_rating_hourly(corresponding_time_ticks, R_rolled, N_rolled, path_to_save=path_to_save)
    path_to_save = os.path.join(RESULT_FOLDER, "lores_hourly_weekday")
    draw_rating_hourly(corresponding_time_ticks, R_rolled, N_rolled, path_to_save=path_to_save, figsize=(12, 6))

    print("Analyze density by time: daily for weeks")
    rolled_timestamps = _roll_timestamps(T, _TimestampFormat.DAILY)
    N_rolled, R_rolled = discretize(X=rolled_timestamps, Y=R, bins=7*24, normalize=False)
    corresponding_time_ticks = np.arange(0, 7*24*60*60, 60*60)
    path_to_save = os.path.join(RESULT_FOLDER, "daily")
    draw_rating_daily(corresponding_time_ticks, R_rolled, N_rolled, path_to_save=path_to_save)
    path_to_save = os.path.join(RESULT_FOLDER, "lores_daily")
    draw_rating_daily(corresponding_time_ticks, R_rolled, N_rolled, path_to_save=path_to_save, figsize=(12, 6))

    print("Analyze density by time: monthly")
    rolled_timestamps = _roll_timestamps(T, _TimestampFormat.MONTHLY)
    N_rolled, R_rolled = discretize(X=rolled_timestamps, Y=R, bins=30*12, normalize=False)
    corresponding_time_ticks = np.arange(0, 30*24*60*60, 2*60*60)
    path_to_save = os.path.join(RESULT_FOLDER, "monthly")
    draw_rating_monthly(corresponding_time_ticks, R_rolled, N_rolled, path_to_save=path_to_save)
    path_to_save = os.path.join(RESULT_FOLDER, "lores_monthly")
    draw_rating_monthly(corresponding_time_ticks, R_rolled, N_rolled, path_to_save=path_to_save, figsize=(12, 6))
