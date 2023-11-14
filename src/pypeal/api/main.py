from typing import Union

from fastapi import FastAPI, HTTPException

from pypeal.api.entities import Peal as PealEntity
from pypeal.peal import Peal

app = FastAPI()


@app.get("/peals/{peal_id}")
def get_peal(peal_id: int) -> PealEntity:
    peal = Peal.get(bellboard_id=peal_id)
    if peal is None:
        raise HTTPException(status_code=404, detail="Peal not found")
    else:
        return PealEntity.from_object(peal)
