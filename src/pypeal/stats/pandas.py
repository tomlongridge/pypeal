from datetime import datetime
import pandas as pd

from pypeal.entities.association import Association
from pypeal.entities.peal import Peal
from pypeal import utils


def peal_to_df(peal: Peal) -> dict:
    return {
        'id': peal.id,
        'date': peal.date,
        'length_type': str(peal.length_type),
        'bellboard_id': peal.bellboard_id,
        'bellboard_url': peal.bellboard_url,
        'bell_type': str(peal.bell_type),
        'association': peal.association,
        'title': peal.title,
        'tower': peal.ring.tower if peal.ring else '',
        'ring': peal.ring,
        'location': peal.location,
        'place': peal.place,
        'county': peal.county,
        'country': peal.country,
        'location_detail': peal.location_detail,
        'duration': str(peal.duration) if peal.duration else '',
        'composer': peal.composer,
        'conductors': peal.conductors,
        'changes': str(peal.changes) if peal.changes else '',
        'ringers': [r for r in peal.ringers],
        'peal': peal
    }


def df_to_sheet_data(df: pd.DataFrame) -> list[list[str]]:
    data = []
    for _, row in df.iterrows():
        data.append([_value_to_str(cell) for cell in row])
    return data


def _value_to_str(value: any) -> str:
    if value is None:
        return ''
    elif type(value) is list:
        return ', '.join([_value_to_str(v) for v in value])
    elif type(value) is Association:
        return value.name
    elif type(value) is bool:
        return 'Yes' if value else 'No'
    elif type(value) is datetime.date:
        return utils.format_date_short(value)
    else:
        return str(value)
