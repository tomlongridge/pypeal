from pypeal.bellboard.consts import BELLBOARD_PEAL_ID_URL, BELLBOARD_PEAL_RANDOM_URL
from pypeal.config import get_config


def get_url_from_id(id: int) -> str:
    return get_config('bellboard', 'url') + (BELLBOARD_PEAL_ID_URL % id if id else BELLBOARD_PEAL_RANDOM_URL)


def get_id_from_url(url: str) -> int:
    if url and url.startswith('http') and url.find('id=') != -1:
        return int(url.split('id=')[1].split('&')[0])
    else:
        return None
