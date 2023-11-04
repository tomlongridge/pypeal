
import re
from pypeal.method import Method, Stage
from pypeal.peal import Peal

METHOD_TITLE_NUM_METHODS_REGEX = re.compile(r'\(([0-9mvp\/])+\)')
METHOD_TITLE_NUM_METHODS_GROUP_REGEX = re.compile(r'([0-9]+[mvp])\/?')

DURATION_REGEX = re.compile(r'^(?:(?P<hours>\d{1,2})[h])$|^(?:(?P<mins>\d+)[m]?)$|' +
                            r'^(?:(?:(?P<hours_2>\d{1,2})[h])\s(?:(?P<mins_2>(?:[0]?|[1-5]{1})[0-9])[m]?))$')
TENOR_INFO_REGEX = re.compile(r'(?P<tenor_weight>[^in]+|size\s[0-9]+)(?:\sin\s(?P<tenor_note>.*))?$')

FOOTNOTE_RINGER_REGEX_PREFIX = re.compile(r'^(?P<bells>[0-9,\s]+)\s?[-:]\s(?P<footnote>.*)$')
FOOTNOTE_RINGER_REGEX_SUFFIX = re.compile(r'^(?P<footnote>.*)\s?[-:]\s(?P<bells>[0-9,\s]+)\.?$')


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

    multi_method_match = None
    if re.search(METHOD_TITLE_NUM_METHODS_REGEX, title):
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


def parse_single_method(method: str, expect_changes: bool = True) -> tuple[Stage, str, str, int]:

    stage: Stage = None
    classification: str = None
    changes: int = None

    method = method.strip(' .,')

    if expect_changes and (match := re.match(r'^(?P<changes>[0-9]+)\s+(?:changes\s)?(?P<method>.*)$', method)):
        changes = int(match.groupdict()['changes'])
        method = match.groupdict()['method'].strip(' .,')

    if (stage := Stage.from_method(method)):
        stage = stage
        method = method[:-len(stage.name)].strip(' .,')

    if method.lower().endswith("treble bob"):
        classification = "Treble Bob"
    elif method.lower().endswith("treble place"):
        classification = "Treble Place"
    elif method.lower().endswith("bob"):
        classification = "Bob"
    elif method.lower().endswith("place"):
        classification = "Place"
    elif method.lower().endswith("surprise"):
        classification = "Surprise"
    elif method.lower().endswith("delight"):
        classification = "Delight"
    elif method.lower().endswith("alliance"):
        classification = "Alliance"
    elif method.lower().endswith("hybrid"):
        classification = "Hybrid"
    if classification:
        method = method[:-len(classification)].strip(' .,')

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
        tenor_note = tenor_info['tenor_note'].strip()
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


def parse_footnote(footnote: str, peal: Peal):
    text = footnote.strip()
    if len(text) > 0:
        if (footnote_match := re.match(FOOTNOTE_RINGER_REGEX_PREFIX, text)) or \
                (footnote_match := re.match(FOOTNOTE_RINGER_REGEX_SUFFIX, text)):
            footnote_info = footnote_match.groupdict()
            text = footnote_info['footnote'].strip()
            bells = [int(bell) for bell in footnote_info['bells'].split(',')]
        else:
            bells = [None]
        peal.add_footnote(bells, text)
