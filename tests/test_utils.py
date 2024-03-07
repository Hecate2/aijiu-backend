from typing import List, Dict
from dateutil import parser
import datetime
from env import ROOT

def is_recent_time(datetime_: str, threshold_seconds = 10):
    """
    :param datetime_: '2024-03-05T12:26:24.295852'
    :param threshold_seconds:
    :return:
    """
    return abs((parser.parse(datetime_) - datetime.datetime.utcnow()).total_seconds()
            - datetime.timedelta(hours=8).total_seconds()) < threshold_seconds

def root_org_only(response: List[Dict[str, str]]):
    assert len(response) == 1
    response = response[0]
    assert response['name'] == ROOT
    assert is_recent_time(response['createTime'])
