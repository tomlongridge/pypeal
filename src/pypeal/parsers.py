
import re
from pypeal.method import Stage
from pypeal.peal import Peal

METHOD_TITLE_NUM_METHODS_REGEX = re.compile(r'\(([0-9mvp\/])+\)')
METHOD_TITLE_NUM_METHODS_GROUP_REGEX = re.compile(r'([0-9]+[mvp])\/?')

DURATION_REGEX = re.compile(r'^(?:(?P<hours>\d{1,2})[h])$|^(?:(?P<mins>\d+)[m]?)$|' +
                            r'^(?:(?:(?P<hours_2>\d{1,2})[h])\s(?:(?P<mins_2>(?:[0]?|[1-5]{1})[0-9])[m]?))$')
TENOR_INFO_REGEX = re.compile(r'(?P<tenor_weight>[^in]+|size\s[0-9]+)(?:\sin\s(?P<tenor_tone>.*))?$')

FOOTNOTE_RINGER_REGEX_PREFIX = re.compile(r'^(?P<bells>[0-9,\s]+)\s?[-:]\s(?P<footnote>.*)$')
FOOTNOTE_RINGER_REGEX_SUFFIX = re.compile(r'^(?P<footnote>.*)\s?[-:]\s(?P<bells>[0-9,\s]+)\.?$')


def parse_method_title(title: str, peal: Peal):

    if title.lower().startswith("mixed"):
        peal.is_mixed = True
        title = title[5:].strip()

    if title.lower().startswith("spliced"):
        peal.is_spliced = True
        title = title[7:].strip()
    else:
        peal.is_spliced = False

    multi_method_match = None
    if re.search(METHOD_TITLE_NUM_METHODS_REGEX, title):
        multi_method_match = re.findall(METHOD_TITLE_NUM_METHODS_GROUP_REGEX, title.strip('()'))
        if len(multi_method_match) > 0:
            for method in multi_method_match:
                match method[-1]:
                    case 'm':
                        peal.num_methods = int(method.removesuffix('m'))
                    case 'v':
                        peal.num_variants = int(method.removesuffix('v'))
                    case 'p':
                        peal.num_principles = int(method.removesuffix('p'))

    title = re.sub(METHOD_TITLE_NUM_METHODS_REGEX, '', title).strip()

    peal.stage, peal.classification, title, _ = parse_single_method(title, expect_changes=False)

    # If there's no title left after parsing, it's a multi-method mixed peal with no number of methods specified
    if len(title) == 0 and not peal.is_spliced:
        peal.is_mixed = True

    peal.title = title if len(title) > 0 else None


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


def parse_tenor_info(tenor_info_str: str) -> tuple[str, str]:
    if not (match := re.match(TENOR_INFO_REGEX, tenor_info_str)):
        raise ValueError(f'Unable to parse tenor info: {tenor_info_str}')
    tenor_weight: str = None
    tenor_tone: str = None
    tenor_info = match.groupdict()
    if tenor_info['tenor_weight']:
        tenor_weight = tenor_info['tenor_weight'].strip()
    if tenor_info['tenor_tone']:
        tenor_tone = tenor_info['tenor_tone'].strip()
    return (tenor_weight, tenor_tone)


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
