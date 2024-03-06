from typing import Dict, List, Union
from sqlalchemy.engine.row import Row
from sqlalchemy import inspect

def jsonify(obj: Union[List[Row], Row, None]) -> Union[List[Dict], Dict, None]:
    if obj is None:
        return None
    if type(obj) is list:
        return [jsonify(i) for i in obj]
    return {k: v for k, v in zip(obj._fields, obj._data)}
    