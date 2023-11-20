import logging
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import RedirectResponse

from pypeal.api.entities import Peal as PealEntity, Ringer as RingerEntity
from pypeal.peal import Peal
from pypeal.ringer import Ringer

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
def get_ringer_peals(ringer_id: int) -> list[PealEntity]:
    ringer = Ringer.get(ringer_id)
    if ringer is None:
        raise HTTPException(status_code=404, detail="Ringer not found")
    return [PealEntity.from_object(peal) for peal in ringer.get_peals()]
