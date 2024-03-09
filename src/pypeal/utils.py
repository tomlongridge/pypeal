from datetime import datetime
import re

NUM_TO_WORD = {
    2: 'two',
    3: 'three',
    4: 'four',
    5: 'five',
    6: 'six',
    7: 'seven',
    8: 'eight',
    9: 'nine',
    10: 'ten',
    11: 'eleven',
    12: 'twelve',
    13: 'thirteen',
    14: 'fourteen',
    15: 'fifteen',
    16: 'sixteen',
    17: 'seventeen',
    18: 'eighteen',
    19: 'nineteen',
    20: 'twenty',
    21: 'twenty-one',
    22: 'twenty-two'
}

WORD_TO_NUM = {
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10,
    'eleven': 11,
    'twelve': 12,
    'thirteen': 13,
    'fourteen': 14,
    'fifteen': 15,
    'sixteen': 16,
    'seventeen': 17,
    'eighteen': 18,
    'nineteen': 19,
    'twenty': 20,
    'twenty-one': 21,
    'twenty-two': 22,
    'second': 2,
    'third': 3,
    'fourth': 4,
    'fifth': 5,
    'sixth': 6,
    'seventh': 7,
    'eighth': 8,
    'ninth': 9,
    'tenth': 10,
    'eleventh': 11,
    'twelfth': 12,
    'thirteenth': 13,
    'fourteenth': 14,
    'fifteenth': 15,
    'sixteenth': 16,
    'seventeenth': 17,
    'eighteenth': 18,
    'nineteenth': 19,
    'twentieth': 20,
    'twenty-first': 21,
    'twenty-second': 22
}

NAME_TITLES = [
    'Mr',
    'Mrs',
    'Miss',
    'Ms',
    'Rev',
    'Revd',
    'Dr',
    'Prof',
    'Sir',
    'Lady',
    'Dame',
    'Lord',
    'Rt Hon',
    'Hon',
    'Preb',
    'Canon',
    'Ven',
    'Fr',
    'Pastor',
    'Bishop',
    'Archbishop',
    'Cardinal',
    'Pope'
]


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


def format_date_full(date: datetime.date) -> str:
    return date.strftime("%A, %-d %B %Y")


def format_date_short(date: datetime.date) -> str:
    return date.strftime("%d-%b-%Y")


def num_to_word(num: int) -> str:
    if num in NUM_TO_WORD:
        return NUM_TO_WORD[num]
    else:
        return None


def word_to_num(word: str) -> str:
    if word is not None and word.lower() in WORD_TO_NUM:
        return WORD_TO_NUM[word.lower()]
    else:
        return None


def get_num_words() -> list[str]:
    return WORD_TO_NUM.keys()


def get_titles() -> list[str]:
    return NAME_TITLES


def get_time_str(mins: int | float) -> str:
    if mins is None:
        return 'Unknown'
    elif mins == 0:
        return '0 mins'
    seconds = ''
    if type(mins) is float:
        seconds = f'{round((mins - int(mins)) * 60)} secs'
        mins = int(mins)
    days = mins // 1440
    hours = mins // 60
    mins = mins % 60
    value = ''
    if days > 0:
        value += f'{round(days)} day{"s" if days > 1 else ""}, '
        hours -= days * 24
    if hours > 0:
        value += f'{round(hours)} hour{"s" if hours > 1 else ""}, '
    if mins > 0:
        value += f'{round(mins)} min{"s" if mins > 1 else ""}, '
    value += seconds
    return value.strip(', ')


def parse_date(text: str) -> datetime.date:
    if text is None:
        return None
    try:
        return datetime.date(datetime.strptime(text, '%Y/%m/%d'))
    except ValueError:
        try:
            return datetime.date(datetime.strptime(text, '%Y-%m-%d'))
        except ValueError:
            return None


def strip_internal_space(value: str) -> str:
    if value is None:
        return None
    new_value = ''
    for word in value.split(' '):
        if len(word) > 0:
            new_value += word.strip() + ' '
    return new_value.strip()


def strip_smart_quotes(value: str) -> str:
    if value is None:
        return None
    return value.replace(u'\u201c', '"') \
                .replace(u'\u201d', '"') \
                .replace(u'\u2018', "'") \
                .replace(u'\u2019', "'")


def get_searchable_string(value: str) -> str:
    if value is None:
        return None
    value = value.lower()
    value = value.replace('single ', '', 1)
    value = value.replace('-', ' ')
    value = value.replace('&', 'and')
    value = re.sub(r'[^\w\d\s]', '', value)
    value = value.replace('  ', ' ')
    return value


def suffix_number(value: int) -> str:
    if value % 10 == 1 and value % 100 != 11:
        return f'{value}st'
    elif value % 10 == 2 and value % 100 != 12:
        return f'{value}nd'
    elif value % 10 == 3 and value % 100 != 13:
        return f'{value}rd'
    else:
        return f'{value}th'
