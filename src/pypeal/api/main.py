from fastapi import FastAPI, HTTPException

from pypeal.api.entities import Peal as PealEntity, Ringer as RingerEntity
from pypeal.peal import Peal
from pypeal.ringer import Ringer

app = FastAPI()


@app.get("/peals/{peal_id}")
def get_peal(peal_id: int) -> PealEntity:
    peal = Peal.get(bellboard_id=peal_id)
    if peal is None:
        raise HTTPException(status_code=404, detail="Peal not found")
    else:
        return PealEntity.from_object(peal)


@app.get("/ringers/{ringer_id}")
def get_ringer(ringer_id: int) -> RingerEntity:
    ringer = Ringer.get(ringer_id)
    if ringer is None:
        raise HTTPException(status_code=404, detail="Ringer not found")
    else:
        return RingerEntity.from_object(ringer)


@app.get("/ringers/{ringer_id}/peals")
def get_ringer_peals(ringer_id: int) -> list[PealEntity]:
    ringer = Ringer.get(ringer_id)
    if ringer is None:
        raise HTTPException(status_code=404, detail="Ringer not found")
    else:
        return [PealEntity.from_object(peal) for peal in ringer.get_peals()]
