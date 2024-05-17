from pypeal.entities.peal import PealLengthType
from pypeal.entities.report import Report
from pypeal.entities.tower import Tower

from haversine import haversine


def get_tower_grab_data(report: Report,
                        length_type: PealLengthType,
                        home_tower: Tower) -> dict[Tower, dict[int, int]]:

    closest_grabs: dict[Tower, (dict[int, int], float)] = {}
    if home_tower is None or home_tower.latitude is None or home_tower.longitude is None:
        home_tower = None
    for tower, grabbed_bells in _get_grabbed_bells(Tower.get_all(), report, length_type).items():
        if home_tower and tower.latitude is not None and tower.longitude is not None:
            distance_mi = haversine((home_tower.latitude, home_tower.longitude), (tower.latitude, tower.longitude), unit='mi')
        else:
            distance_mi = None
        closest_grabs[tower] = (grabbed_bells, distance_mi)

    # Order by distance then name
    return {tower: (bells, distance) for tower, (bells, distance) in
            dict(sorted(closest_grabs.items(), key=lambda x: (x[1][1] or 1000000, str(x[0])))).items()}


def _get_grabbed_bells(towers: list[Tower], report: Report, length_type: PealLengthType) -> dict[Tower, dict[int, int]]:

    tower_data: dict[Tower, dict[int, int]] = {}
    for tower in towers:
        if (tower_bells := tower.get_active_ring().bells):
            tower_data[tower] = {b.id: 0 for b in tower_bells.values()}

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
