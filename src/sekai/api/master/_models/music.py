from datetime import datetime

from sekai.core.models import ToSharedModel
from sekai.core.models.chara import Character as SharedCharacter
from sekai.core.models.chara import CharacterType
from sekai.core.models.live import LiveDifficulty, LiveInfo
from sekai.core.models.music import MusicInfo, MusicVersion, VocalType

from . import TIMEZONE, BaseSchema

VOCAL_TYPES = {
    "original_song": VocalType.VIRTUAL_SINGER,
    "virtual_singer": VocalType.VIRTUAL_SINGER,
    "sekai": VocalType.SEKAI,
}


CHARACTER_TYPES = {
    "game_character": CharacterType.GAME,
    "outside_character": CharacterType.EXTRA,
}


class Character(BaseSchema):
    id: int
    music_id: int
    music_vocal_id: int
    character_type: str
    character_id: int
    seq: int


class MusicVocal(BaseSchema, ToSharedModel[MusicVersion]):
    id: int
    music_id: int
    music_vocal_type: str
    seq: int
    release_condition_id: int
    caption: str
    characters: list[Character]
    assetbundle_name: str
    archive_published_at: int | None = None

    def to_shared_model(self) -> MusicVersion:
        singers = [
            SharedCharacter(id=chara.character_id, type=CHARACTER_TYPES[chara.character_type])
            for chara in self.characters
        ]
        return MusicVersion(
            id=self.id,
            music_id=self.music_id,
            vocal_type=VOCAL_TYPES.get(self.music_vocal_type, VocalType.OTHER),
            singers=singers,
            asset_id=self.assetbundle_name,
        )


class Music(BaseSchema, ToSharedModel[MusicInfo]):
    id: int
    seq: int
    release_condition_id: int
    categories: list[str]
    title: str
    pronunciation: str
    creator_artist_id: int
    lyricist: str
    composer: str
    arranger: str
    dancer_count: int
    self_dancer_position: int
    assetbundle_name: str
    live_talk_background_assetbundle_name: str
    published_at: int
    released_at: int
    live_stage_id: int
    filler_sec: float
    is_newly_written_music: bool

    def to_shared_model(self) -> MusicInfo:
        return MusicInfo(
            id=self.id,
            title=self.title,
            lyricist=self.lyricist,
            composer=self.composer,
            arranger=self.arranger,
            released=datetime.fromtimestamp(self.released_at / 1000, TIMEZONE),
            published=datetime.fromtimestamp(self.published_at / 1000, TIMEZONE),
            asset_id=self.assetbundle_name,
        )


class MusicDifficulty(BaseSchema, ToSharedModel[LiveInfo]):
    id: int
    music_id: int
    music_difficulty: str
    play_level: int
    release_condition_id: int
    total_note_count: int

    def to_shared_model(self) -> LiveInfo:
        return LiveInfo(
            id=self.id,
            music_id=self.music_id,
            difficulty=LiveDifficulty[self.music_difficulty.upper()],
            level=self.play_level,
        )
