
import re
from pypeal import utils
from pypeal.method import Classification, Method, Stage

METHOD_TITLE_MIXED_METHODS_REGEX = \
    re.compile(r'^(?P<num_methods>[0-9]+|' + '|'.join(utils.get_num_words()) + r')+ ' +
               r'(?P<classification>' + '|'.join([s.name for s in Classification]) + r')?\s?' +
               r'(?P<stage>' + '|'.join([s.name for s in Stage]) + ')',
               re.IGNORECASE)

# Match either a number and one of m, v or p as part of the title or, if in brackets, then allow just m, v or p with no number
# (e.g. (11m/v/p)) as this would be liable to match too much in normal text
METHOD_TITLE_NUM_METHODS_REGEX = re.compile(r'(([0-9]+[mvp]\/?)+)|\(([0-9]*[mvp]\/?)+\)')
METHOD_TITLE_NUM_METHODS_GROUP_REGEX = re.compile(r'([0-9]+[mvp])\/?')

DURATION_REGEX = re.compile(r'^(?:(?P<hours>\d{1,2})[h])$|^(?:(?P<mins>\d+)[m]?)$|' +
                            r'^(?:(?:(?P<hours_2>\d{1,2})[h])\s(?:(?P<mins_2>(?:[0]?|[1-5]{1})[0-9])[m]?))$')
TENOR_INFO_REGEX = re.compile(r'(?P<tenor_weight>[^in]+|size\s[0-9]+)(?:\sin\s(?P<tenor_note>.*))?$')

FOOTNOTE_RINGER_SEPARATORS = [' ', ',', '&', 'and']
FOOTNOTE_RINGER_REGEX_PREFIX = re.compile(r'^(?P<bells>(?:(?:(?:[0-9]+(?:st|nd|rd|th)?)|' +
                                          r'(?:treble|tenor|' + '|'.join(utils.get_num_words()) + r'))\s?(?:' +
                                          '|'.join(FOOTNOTE_RINGER_SEPARATORS) +
                                          r')?\s?)+)' +
                                          r'\s?[-:]\s?(?P<footnote>.*)\.?$', re.IGNORECASE)
FOOTNOTE_RINGER_REGEX_SUFFIX = re.compile(r'^(?P<footnote>.*)\s?[-:]\s?(?P<bells>(?:(?:(?:[0-9]+(?:st|nd|rd|th)?)|' +
                                          r'(?:treble|tenor|' + '|'.join(utils.get_num_words()) + r'))\s?(?:' +
                                          '|'.join(FOOTNOTE_RINGER_SEPARATORS) +
                                          r')?\s?)+)' +
                                          r'\.?$', re.IGNORECASE)
FOOTNOTE_CONDUCTOR_REGEX = re.compile(r'.*as conductor.*', re.IGNORECASE)
FOOTNOTE_COMPOSER_REGEX = re.compile(r'.*composed by\s(?P<composer>.*)$', re.IGNORECASE)
FOOTNOTE_ALL_BAND_REGEX = \
    re.compile(r'.*(?:for|by) all(?: the band)?(?: (?:except for|except|apart from)(?: the)? (?P<exceptions>[^\.]+))?', re.IGNORECASE)


def parse_method_title(title: str) -> tuple[Method, bool, bool, int, int, int]:

    method: Method = Method()
    is_spliced: bool = None
    is_mixed: bool = None
    num_methods: int = None
    num_variants: int = None
    num_principles: int = None

    if title.lower().startswith('mixed'):
        is_spliced = False
        is_mixed = True
        title = title[5:].strip()

    if title.lower().startswith('spliced'):
        is_spliced = True
        is_mixed = False
        title = title[7:].strip()
    else:
        is_spliced = False  # It's not spliced if it doesn't say in title (unlike mixed)

    # Catch titles such as "12 Doubles"
    if match := re.match(METHOD_TITLE_MIXED_METHODS_REGEX, title):
        is_mixed = True
        match_details = match.groupdict()
        method.stage = Stage.from_method(match_details['stage'])
        method.classification = Classification(match_details['classification']) if match_details['classification'] else None
        if match_details['num_methods'].isnumeric():
            num_methods = int(match_details['num_methods'])
        else:
            num_methods = utils.word_to_num(match_details['num_methods'])
        title = title[len(match_details['num_methods']) + 1:].strip()

    # Parse m/v/p detail in brackets
    elif re.search(METHOD_TITLE_NUM_METHODS_REGEX, title):
        multi_method_match = re.findall(METHOD_TITLE_NUM_METHODS_GROUP_REGEX, title.strip('()'))
        if len(multi_method_match) > 0:
            is_mixed = not is_spliced
            num_methods = num_variants = num_principles = 0
            for multi_method in multi_method_match:
                match multi_method[-1]:
                    case 'm':
                        num_methods = int(multi_method.removesuffix('m'))
                    case 'v':
                        num_variants = int(multi_method.removesuffix('v'))
                    case 'p':
                        num_principles = int(multi_method.removesuffix('p'))

        title = re.sub(METHOD_TITLE_NUM_METHODS_REGEX, '', title).strip()

    method.stage, method.classification, title, _ = parse_single_method(title, expect_changes=False)

    if title.lower().endswith('little'):
        method.is_little = True
        title = title[:-6].strip()
    elif title.lower().endswith('differential'):
        method.is_differential = True
        title = title[:-12].strip()
    elif title.lower().endswith('treble dodging'):
        method.is_treble_dodging = True
        title = title[:-13].strip()

    # If there's no title left after parsing, it's a multi-method mixed peal with no number of methods specified
    # (exception – Little Bob)
    if is_spliced is not True and len(title) == 0 and method.is_little is not True:
        is_mixed = True

    method.name = title if len(title) > 0 else None

    return (method, is_spliced, is_mixed, num_methods, num_variants, num_principles)


def parse_single_method(method: str, expect_changes: bool = True) -> tuple[Stage, Classification, str, int]:

    stage: Stage = None
    classification: Classification = None
    changes: int = None

    method = method.strip(' .,')

    if expect_changes and (match := re.match(r'^(?P<changes>[0-9]+)\s+(?:changes\s)?(?P<method>.*)$', method)):
        changes = int(match.groupdict()['changes'])
        method = match.groupdict()['method'].strip(' .,')

    if (stage := Stage.from_method(method)):
        stage = stage
        method = method[:-len(stage.name)].strip(' .,')

    if method.lower().endswith("treble bob"):
        classification = Classification("Treble Bob")
    elif method.lower().endswith("treble place"):
        classification = Classification("Treble Place")
    elif method.lower().endswith("bob"):
        classification = Classification("Bob")
    elif method.lower().endswith("place"):
        classification = Classification("Place")
    elif method.lower().endswith("surprise"):
        classification = Classification("Surprise")
    elif method.lower().endswith("delight"):
        classification = Classification("Delight")
    elif method.lower().endswith("alliance"):
        classification = Classification("Alliance")
    elif method.lower().endswith("hybrid"):
        classification = Classification("Hybrid")
    if classification:
        method = method[:-len(classification.value)].strip(' .,')

    return (stage, classification, method, changes)


def parse_tenor_info(tenor_info_str: str) -> tuple[int, str]:
    if not (match := re.match(TENOR_INFO_REGEX, tenor_info_str)):
        raise ValueError(f'Unable to parse tenor info: {tenor_info_str}')
    tenor_weight: int = None
    tenor_note: str = None
    tenor_info = match.groupdict()
    if tenor_info['tenor_weight']:
        tenor_weight = parse_bell_weight(tenor_info['tenor_weight'])
    if tenor_info['tenor_note']:
        tenor_note = utils.convert_musical_key(tenor_info['tenor_note'].strip())
    return (tenor_weight, tenor_note)


def parse_bell_weight(weight_str: str) -> int:
    if weight_str is None:
        return None
    weight_lbs = None
    weight_str = weight_str.replace('–', '-').strip()
    if weight_str.endswith('cwt'):
        weight_lbs = int(weight_str[:-3]) * 112
    elif re.match(r'^[0-9]+(\-[0-9]+\-[0-9]+)?$', weight_str):
        weight_parts = weight_str.split('-')
        weight_lbs = int(weight_parts[0]) * 112
        if len(weight_parts) > 1:
            weight_lbs += int(int(weight_parts[1]) * (112/4))
            weight_lbs += int(weight_parts[2])
    else:
        raise ValueError(f'Unable to parse weight: {weight_str}')
    return weight_lbs


def parse_duration(duration_str: str) -> int:
    if not (duration_match := re.search(DURATION_REGEX, duration_str.strip())):
        raise ValueError(f'Unable to parse duration: {duration_str}')
    duration_info = duration_match.groupdict()
    duration = int(duration_info['hours'] or 0) * 60
    duration += int(duration_info['hours_2'] or 0) * 60
    duration += int(duration_info['mins'] or 0)
    duration += int(duration_info['mins_2'] or 0)
    return duration


def parse_footnote(footnote: str, num_bells: int, conductor_bells: list[int]) -> tuple[list[int], str]:
    bells = []
    not_bells = []
    text = footnote.strip(' .')
    if len(text) > 0:
        if (footnote_match := re.match(FOOTNOTE_RINGER_REGEX_PREFIX, text)) or \
                (footnote_match := re.match(FOOTNOTE_RINGER_REGEX_SUFFIX, text)):
            footnote_info = footnote_match.groupdict()
            text = footnote_info['footnote'].strip()
            bells = []
            for bell in re.split('|'.join(FOOTNOTE_RINGER_SEPARATORS), footnote_info['bells']):
                if len(bell) == 0:
                    continue
                elif bell[0].isnumeric():
                    bell = bell.replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                    bells.append(int(bell))
                elif utils.word_to_num(bell) is not None:
                    bells.append(utils.word_to_num(bell))
                elif bell.lower() == 'treble':
                    bells.append(1)
                elif bell.lower() == 'tenor':
                    bells.append(num_bells)
        text += '.'
        if re.match(FOOTNOTE_CONDUCTOR_REGEX, text):
            bells += conductor_bells
        if all_band_match := re.match(FOOTNOTE_ALL_BAND_REGEX, text):
            bells += range(1, num_bells + 1)
            excluded_ringers = all_band_match.groupdict()['exceptions']
            if excluded_ringers is not None:
                if 'conductor' in excluded_ringers:
                    not_bells += conductor_bells
                    excluded_ringers = excluded_ringers.replace('the conductor', '')
                    excluded_ringers = excluded_ringers.replace('conductor', '')
                for bell in re.split('|'.join(FOOTNOTE_RINGER_SEPARATORS), excluded_ringers):
                    if len(bell) > 0:
                        not_bells += [int(bell)]
        bells = [bell for bell in bells if bell not in not_bells]
    else:
        text = None
    return (sorted(bells) if len(bells) > 0 else None, text)


def parse_footnote_for_composer(footnote: str) -> str:
    if composer_match := re.match(FOOTNOTE_COMPOSER_REGEX, footnote):
        return composer_match.groupdict()['composer']
