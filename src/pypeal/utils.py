from datetime import datetime

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
    'twenty-two': 22
}


def split_full_name(full_name: str) -> tuple[str, str]:
    if not full_name:
        return None
    elif ' ' in full_name:
        last_name = full_name.split(' ')[-1]
        given_names = ' '.join(full_name.split(' ')[:-1])
        return last_name, given_names
    else:
        return full_name, None


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


def num_to_word(num: int) -> str:
    if num in NUM_TO_WORD:
        return NUM_TO_WORD[num]
    else:
        return None


def word_to_num(word: str) -> str:
    if word in NUM_TO_WORD:
        return WORD_TO_NUM[word]
    else:
        return None


def get_num_words() -> list[str]:
    return WORD_TO_NUM.keys()
