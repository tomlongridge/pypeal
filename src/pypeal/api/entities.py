from pydantic import BaseModel, computed_field

from pypeal.entities.association import Association as AssociationDataClass
from pypeal.entities.peal import Peal as PealDataClass
from pypeal.entities.method import Method as MethodDataClass
from pypeal.entities.ringer import Ringer as RingerDataClass
from pypeal.entities.tower import Tower as TowerDataClass, Ring as RingDataClass, Bell as BellDataClass


class Association(BaseModel):
    id: int
    name: str

    @classmethod
    def from_object(cls, association: AssociationDataClass):
        return cls(
            id=association.id,
            name=association.name
        )


class RingerBasic(BaseModel):
    id: int
    last_name: str
    given_names: str | None

    @computed_field
    @property
    def url(self) -> str:
        return f'/ringers/{self.id}/'

    @computed_field
    @property
    def peals(self) -> str:
        return f'/ringers/{self.id}/peals'

    @classmethod
    def from_object(cls, ringer: RingerDataClass):
        return cls(
            id=ringer.id,
            last_name=ringer.last_name,
            given_names=ringer.given_names,
        )


class Ringer(RingerBasic):
    aliases: list[str]

    @classmethod
    def from_object(cls, ringer: RingerDataClass):
        return cls(
            id=ringer.id,
            last_name=ringer.last_name,
            given_names=ringer.given_names,
            aliases=ringer.aliases,
        )


class CompositionDetail(BaseModel):
    composer: RingerBasic | None
    url: str | None

    @classmethod
    def from_object(cls, peal: PealDataClass):
        return cls(
            composer=RingerBasic.from_object(peal.composer) if peal.composer else None,
            url=peal.composition_url,
        )


class FootnoteDetail(BaseModel):
    text: str
    bell: int | None
    ringer: RingerBasic | None


class Bell(BaseModel):
    id: int
    role: int | None
    weight: int | None
    note: str | None
    cast_year: int | None
    founder: str | None

    @classmethod
    def from_object(cls, bell: BellDataClass):
        return cls(
            id=bell.id,
            role=bell.role,
            weight=bell.weight,
            note=bell.note,
            cast_year=bell.cast_year,
            founder=bell.founder,
        )


class Ring(BaseModel):

    id: int
    tower_id: int
    description: str | None
    date_removed: str | None
    bells: list[Bell]

    @computed_field
    @property
    def url(self) -> str:
        return f'/towers/{self.tower_id}/rings/{self.id}'

    @computed_field
    @property
    def peals(self) -> str:
        return f'/towers/{self.tower_id}/rings/{self.id}/peals'

    @classmethod
    def from_object(cls, ring: RingDataClass):
        return cls(
            id=ring.id,
            tower_id=ring.tower.id,
            description=ring.description,
            date_removed=ring.date_removed.strftime('%Y/%m/%d') if ring.date_removed else None,
            bells=[Bell.from_object(bell) for bell in ring.bells.values()]
        )


class TowerBasic(BaseModel):
    id: int
    towerbase_id: int | None

    @computed_field
    @property
    def url(self) -> str:
        return f'/towers/{self.id}/'

    @classmethod
    def from_object(cls, tower: TowerDataClass):
        return cls(
            id=tower.id,
            towerbase_id=tower.towerbase_id,
        )


class Tower(TowerBasic):
    place: str
    sub_place: str | None
    dedication: str | None
    county: str
    country: str
    country_code: str
    latitude: float | None
    longitude: float | None
    rings: list[Ring]

    @classmethod
    def from_object(cls, tower: TowerDataClass):
        return cls(
            id=tower.id,
            towerbase_id=tower.towerbase_id,
            place=tower.place,
            sub_place=tower.sub_place,
            dedication=tower.dedication,
            county=tower.county,
            country=tower.country,
            country_code=tower.country_code,
            latitude=tower.latitude,
            longitude=tower.longitude,
            rings=[Ring.from_object(ring) for ring in tower.rings],
        )


class Location(BaseModel):
    country: str | None
    county: str | None
    place: str | None
    sub_place: str | None
    address: str | None
    dedication: str | None
    tower: TowerBasic | None

    @classmethod
    def from_object(cls, peal: PealDataClass):
        return cls(
            country=peal.country,
            county=peal.county,
            place=peal.place,
            sub_place=peal.sub_place,
            address=peal.address,
            dedication=peal.dedication,
            tower=TowerBasic.from_object(peal.ring.tower) if peal.ring else None,
        )


class Method(BaseModel):
    id: str
    name: str | None
    classification: str | None
    stage: int | None

    @classmethod
    def from_object(cls, method: MethodDataClass):
        return cls(
            id=method.id,
            name=method.name,
            classification=method.classification.value if method.classification else None,
            stage=method.stage.value if method.stage else None,
        )


class MethodDetail(BaseModel):
    changes: int | None
    method: Method | None


class PhotoDetail(BaseModel):
    caption: str | None
    credit: str | None
    original_url: str
    url: str


class PerformanceDetail(BaseModel):
    changes: int | None
    num_methods: int | None
    num_principles: int | None
    num_variants: int | None
    stage: int | None
    classification: str | None
    is_variable_cover: bool
    methods: list[MethodDetail] | None
    title: str | None
    published_title: str | None
    detail: str | None
    photos: list[PhotoDetail] | None
    external_reference: str | None

    @classmethod
    def from_object(cls, peal: PealDataClass):
        if peal.method:
            methods = [MethodDetail(changes=peal.changes, method=Method.from_object(peal.method))]
        elif peal.methods:
            methods = [MethodDetail(changes=method[1], method=Method.from_object(method[0])) for method in peal.methods]
        else:
            methods = []
        if peal.photos:
            photos = [PhotoDetail(caption=photo[1],
                                  credit=photo[2],
                                  original_url=photo[3],
                                  url=f'/peals/{peal.bellboard_id}/photos/{i}')
                      for i, photo in enumerate(peal.photos)]
        else:
            photos = None
        return cls(
            changes=peal.changes,
            num_methods=peal.num_methods,
            num_principles=peal.num_principles,
            num_variants=peal.num_variants,
            stage=peal.stage.value if peal.stage else None,
            classification=peal.classification.value if peal.classification else None,
            is_variable_cover=peal.is_variable_cover,
            methods=methods,
            title=peal.title,
            published_title=peal.published_title,
            detail=peal.detail,
            photos=photos,
            external_reference=peal.external_reference,
        )


class PealRinger(BaseModel):
    bell_roles: list[int] | None
    nums: list[int] | None
    ringer: RingerBasic
    is_conductor: bool
    note: str | None


class PealBase(BaseModel):
    id: int
    bellboard_id: int | None
    date: str
    type: str
    length_type: str | None
    bell_type: str

    @computed_field
    @property
    def url(self) -> str:
        return f'/peals/{self.id}/'

    @classmethod
    def from_object(cls, peal: PealDataClass):
        return cls(
            id=peal.id,
            bellboard_id=peal.bellboard_id,
            date=peal.date.strftime('%Y/%m/%d'),
            type=peal.type.name,
            length_type=peal.length_type.name if peal.length_type else None,
            bell_type=peal.bell_type.name if peal.bell_type else None,
        )


class PealBasic(PealBase):
    location: str
    changes: int | None
    title: str

    @classmethod
    def from_object(cls, peal: PealDataClass):
        return cls(
            id=peal.id,
            bellboard_id=peal.bellboard_id,
            date=peal.date.strftime('%Y/%m/%d'),
            type=peal.type.name,
            length_type=peal.length_type.name if peal.length_type else None,
            bell_type=peal.bell_type.name if peal.bell_type else None,
            location=peal.location,
            changes=peal.changes,
            title=peal.title
        )


class Peal(PealBase):
    association: Association | None
    location: Location
    performance: PerformanceDetail
    composition: CompositionDetail
    duration: int | None
    event_url: str | None
    muffles: str | None
    ringers: list[PealRinger] | None
    footnotes: list[FootnoteDetail]

    @classmethod
    def from_object(cls, peal: PealDataClass):
        ringers = []
        for ringer in peal.ringers:
            bells = None
            if peal.ring and ringer.bell_ids:
                bells = []
                for bell_id in ringer.bell_ids:
                    bells.append(peal.ring.get_bell_by_id(bell_id).role)
            ringers.append(
                PealRinger(bell_roles=bells,
                           nums=ringer.bell_nums,
                           ringer=RingerBasic.from_object(ringer.ringer),
                           is_conductor=ringer.is_conductor,
                           note=ringer.note)
            )
        return cls(
            id=peal.id,
            bellboard_id=peal.bellboard_id,
            type=peal.type.name,
            length_type=peal.length_type.name if peal.length_type else None,
            bell_type=peal.bell_type.name if peal.bell_type else None,
            date=peal.date.strftime('%Y/%m/%d'),
            duration=peal.duration,
            association=Association.from_object(peal.association) if peal.association else None,
            location=Location.from_object(peal),
            performance=PerformanceDetail.from_object(peal),
            composition=CompositionDetail.from_object(peal),
            muffles=peal.muffles,
            ringers=ringers,
            footnotes=[
                FootnoteDetail(text=footnote.text,
                               bell=footnote.bell,
                               ringer=RingerBasic.from_object(footnote.ringer) if footnote.ringer else None)
                for footnote in peal.footnotes],
            event_url=peal.event_url,
        )
