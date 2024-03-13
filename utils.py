from typing import Dict, List, Union
import datetime
from sqlalchemy.engine.row import Row

def jsonify(obj: Union[List[Row], Row, None]) -> Union[List[Dict], Dict, None]:
    if obj is None:
        return None
    if type(obj) is list:
        return [jsonify(i) for i in obj]
    return {k: v for k, v in zip(obj._fields, obj._data)}

def datetime_to_string(dt: datetime.datetime) -> str:
    return dt.strftime('%Y/%m/%d, %H:%M:%S')

def datetime_utc_8() -> datetime.datetime:
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)
