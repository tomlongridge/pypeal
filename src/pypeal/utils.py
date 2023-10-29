def split_full_name(full_name: str) -> tuple[str, str]:
    last_name = full_name.split(' ')[-1]
    given_names = ' '.join(full_name.split(' ')[:-1])
    return last_name, given_names


def get_bell_label(bells: list[int]) -> str:
    if bells and len(bells) >= 1:
        return ','.join([str(bell) for bell in bells])
    else:
        return ''
