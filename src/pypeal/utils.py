from datetime import datetime


def split_full_name(full_name: str) -> tuple[str, str]:
    last_name = full_name.split(' ')[-1]
    given_names = ' '.join(full_name.split(' ')[:-1])
    return last_name, given_names


def get_bell_label(bells: list[int]) -> str:
    if bells and len(bells) >= 1:
        return ','.join([str(bell) for bell in bells])
    else:
        return ''


def get_weight_str(lbs: int) -> str:
    if lbs is None:
        return 'Unknown'
    cwt = lbs // 112
    lbs = lbs % 112
    if lbs / 112 >= 0.75:
        qtr = 3
    elif lbs / 112 >= 0.5:
        qtr = 2
    elif lbs / 112 >= 0.25:
        qtr = 1
    else:
        qtr = 0
    lbs -= qtr * 28
    if qtr == lbs == 0:
        return f'{cwt} cwt'
    else:
        return f'{cwt}-{qtr}-{lbs}'


def convert_musical_key(key: str):
    return key.replace('\u266D', 'b').replace('\u266F', '#') if key else None


def format_date_full(date: datetime) -> str:
    return date.strftime("%A, %-d %B %Y")
