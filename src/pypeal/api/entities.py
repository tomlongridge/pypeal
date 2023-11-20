from pydantic import BaseModel

from pypeal.association import Association as AssociationDataClass
from pypeal.peal import Peal as PealDataClass
from pypeal.method import Method as MethodDataClass
from pypeal.ringer import Ringer as RingerDataClass


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

    @classmethod
    def from_object(cls, ringer: RingerDataClass):
        return cls(
            id=ringer.id,
            last_name=ringer.last_name,
            given_names=ringer.given_names,
        )


class Ringer(RingerBasic):
    aliases: list[RingerBasic]

    @classmethod
    def from_object(cls, ringer: RingerDataClass):
        return cls(
            id=ringer.id,
            last_name=ringer.last_name,
            given_names=ringer.given_names,
            aliases=[RingerBasic.from_object(alias) for alias in ringer.get_aliases()],
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


class Location(BaseModel):
    country: str | None
    county: str | None
    place: str | None
    sub_place: str | None
    address: str | None
    dedication: str | None

    @classmethod
    def from_object(cls, peal: PealDataClass):
        return cls(
            country=peal.country,
            county=peal.county,
            place=peal.place,
            sub_place=peal.sub_place,
            address=peal.address,
            dedication=peal.dedication,
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
    title: str
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
        )


class PealRinger(BaseModel):
    bells: list[int] | None
    bell_nums: list[int] | None
    ringer: RingerBasic
    is_conductor: bool


class Peal(BaseModel):
    id: int
    bellboard_id: int
    date: str
    type: str
    length_type: str | None
    bell_type: str
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
        return cls(
            id=peal.id,
            bellboard_id=peal.bellboard_id,
            type=peal.type.name,
            length_type=peal.length_type.name if peal.length_type else None,
            bell_type=peal.bell_type.name if peal.bell_type else None,
            date=peal.date.strftime('%Y-%m-%d'),
            duration=peal.duration,
            association=Association.from_object(peal.association) if peal.association else None,
            location=Location.from_object(peal),
            performance=PerformanceDetail.from_object(peal),
            composition=CompositionDetail.from_object(peal),
            muffles=peal.muffles,
            ringers=[
                PealRinger(bells=ringer[1],
                           bell_nums=ringer[2],
                           ringer=RingerBasic.from_object(ringer[0]),
                           is_conductor=ringer[3])
                for ringer in peal.ringers] if peal.ringers else None,
            footnotes=[
                FootnoteDetail(text=footnote[0],
                               bell=footnote[1],
                               ringer=RingerBasic.from_object(footnote[2]) if footnote[2] else None)
                for footnote in peal.footnotes],
            event_url=peal.event_url,
        )
