import logging
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import RedirectResponse

from pypeal.api.entities import Peal as PealEntity, PealBasic as PealBasicEntity
from pypeal.api.entities import Ringer as RingerEntity
from pypeal.api.entities import Tower as TowerEntity, Ring as RingEntity
from pypeal.entities.peal import Peal
from pypeal.entities.ringer import Ringer
from pypeal.entities.tower import Tower, Ring

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

app = FastAPI()


@app.get("/bellboard/{bellboard_id}", response_class=RedirectResponse, status_code=301)
def get_peal_by_bellboard_id(bellboard_id: int) -> RedirectResponse:
    peal = Peal.get(bellboard_id=bellboard_id)
    if peal is None:
        raise HTTPException(status_code=404, detail="Peal not found")
    return RedirectResponse(url=f'/peals/{peal.id}')


@app.get("/peals/{peal_id}")
def get_peal(peal_id: int) -> PealEntity:
    peal = Peal.get(id=peal_id)
    if peal is None:
        raise HTTPException(status_code=404, detail="Peal not found")
    return PealEntity.from_object(peal)


@app.get("/peals/{peal_id}/photos/{photo_index}",
         responses={
             200: {
                 "content": {"image/jpg": {}}
             }},
         response_class=Response)
def get_peal_photo(peal_id: int, photo_index: int) -> str:
    peal = Peal.get(bellboard_id=peal_id)
    if peal is None:
        raise HTTPException(status_code=404, detail="Peal not found")
    if photo_index > len(peal.photos) - 1:
        raise HTTPException(status_code=404, detail="Peal photo not found")
    return Response(content=peal.get_photo_bytes(peal.photos[photo_index][1]), media_type="image/jpg")


@app.get("/ringers/{ringer_id}")
def get_ringer(ringer_id: int) -> RingerEntity:
    ringer = Ringer.get(ringer_id)
    if ringer is None:
        raise HTTPException(status_code=404, detail="Ringer not found")
    return RingerEntity.from_object(ringer)


@app.get("/ringers/{ringer_id}/peals")
def get_ringer_peals(ringer_id: int) -> list[PealBasicEntity]:
    ringer = Ringer.get(ringer_id)
    if ringer is None:
        raise HTTPException(status_code=404, detail="Ringer not found")
    return [PealBasicEntity.from_object(peal) for peal in ringer.get_peals()]


@app.get("/towers/{tower_id}")
def get_tower(tower_id: int) -> TowerEntity:
    tower = Tower.get(tower_id)
    if tower is None:
        raise HTTPException(status_code=404, detail="Tower not found")
    return TowerEntity.from_object(tower)


@app.get("/towers/{tower_id}/peals")
def get_tower_peals(tower_id: int) -> list[PealBasicEntity]:
    tower = Tower.get(tower_id)
    if tower is None:
        raise HTTPException(status_code=404, detail="Tower not found")
    return [PealBasicEntity.from_object(peal) for peal in tower.get_peals()]


@app.get("/towers/{tower_id}/rings")
def get_tower_rings(tower_id: int) -> list[RingEntity]:
    tower = Tower.get(tower_id)
    if tower is None:
        raise HTTPException(status_code=404, detail="Tower not found")
    return [RingEntity.from_object(ring) for ring in tower.rings]


@app.get("/towers/{tower_id}/rings/{ring_id}")
def get_tower_ring(tower_id: int, ring_id: int) -> RingEntity:
    tower = Tower.get(tower_id)
    if tower is None:
        raise HTTPException(status_code=404, detail="Tower not found")
    ring = Ring.get(ring_id)
    if ring is None:
        raise HTTPException(status_code=404, detail="Ring not found")
    return RingEntity.from_object(ring)


@app.get("/towers/{tower_id}/rings/{ring_id}/peals")
def get_tower_ring_peals(tower_id: int, ring_id: int) -> list[PealBasicEntity]:
    tower = Tower.get(tower_id)
    if tower is None:
        raise HTTPException(status_code=404, detail="Tower not found")
    ring = Ring.get(ring_id)
    if ring is None:
        raise HTTPException(status_code=404, detail="Ring not found")
    return [PealBasicEntity.from_object(peal) for peal in ring.get_peals()]
