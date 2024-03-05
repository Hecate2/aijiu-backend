from dateutil import parser
import datetime

def is_recent_time(datetime_: str, threshold_seconds = 10):
    """
    :param datetime_: '2024-03-05T12:26:24.295852'
    :param threshold_seconds:
    :return:
    """
    return abs((parser.parse(datetime_) - datetime.datetime.utcnow()).total_seconds()
            - datetime.timedelta(hours=8).total_seconds()) < threshold_seconds