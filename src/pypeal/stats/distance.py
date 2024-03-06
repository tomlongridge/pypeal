import logging
from pypeal.entities.peal import PealLengthType
from pypeal.entities.report import Report
from pypeal.entities.tower import Bell, Tower

from haversine import haversine

logger = logging.getLogger('pypeal')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')

fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)


def get_grabbed_towers(towers: list[Tower], report: Report, length_type: PealLengthType) -> dict[Tower, dict[int, int]]:

    tower_data: dict[Tower, dict[int, int]] = {}
    for tower in towers:
        tower_data[tower] = {b.id: 0 for b in tower.get_active_ring().bells.values()}

    for peal in report.get_peals(length_type=length_type):
        if peal.ring is None:
            continue
        if peal.ring.tower not in tower_data:
            continue
        if peal.ring.id != peal.ring.tower.get_active_ring().id:
            continue
        for peal_ringer in peal.ringers:
            if peal_ringer.ringer.id == report.ringer.id and peal_ringer.bell_ids:
                for bell_id in peal_ringer.bell_ids:
                    if bell_id not in tower_data[peal.ring.tower]:
                        print(f'Bell {bell_id} not found in tower {peal.ring.tower.name}')
                        continue
                    tower_data[peal.ring.tower][bell_id] += 1

    return tower_data


def get_closest_grabs(report: Report,
                      length_type: PealLengthType,
                      home_tower: Tower,
                      max_distance_mi: float = 10.0) -> dict[Tower, (dict[int, int], float)]:

    towers_in_range: dict[Tower, float] = {}
    for tower in Tower.get_all():
        if tower.latitude is None or tower.longitude is None:
            continue
        distance_mi = haversine((home_tower.latitude, home_tower.longitude), (tower.latitude, tower.longitude), unit='mi')
        if distance_mi < max_distance_mi:
            towers_in_range[tower] = distance_mi

    closest_grabs: dict[Tower, (dict[int, int], float)] = {}
    for tower, grabbed_bells in get_grabbed_towers(towers_in_range.keys(), report, length_type).items():
        closest_grabs[tower] = (grabbed_bells, towers_in_range[tower])

    return dict(sorted(closest_grabs.items(), key=lambda x: x[1][1]))  # Order by distance


grabbed_towers = get_closest_grabs(Report.get('Tom'), PealLengthType.QUARTER_PEAL, Tower.get(dove_id=13019))
for tower, (grabbed_bells, distance) in grabbed_towers.items():
    ungrabbed_bells = [Bell.get(b).role for b, c in grabbed_bells.items() if c == 0]
    if len(ungrabbed_bells) > 0:
        print(f'[{distance:.2f} miles] {tower.name}: {ungrabbed_bells}')
