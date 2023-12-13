from typing import cast

from sekai.core.models import ToSharedModel
from sekai.core.models.card import Card, Deck
from sekai.core.models.card import TotalPower as SharedTotalPower
from sekai.core.models.user import Profile as SharedProfile
from sekai.core.models.user import UserInfo
from sekai.utils import iters

from . import BaseSchema


class TotalPower(BaseSchema, ToSharedModel[SharedTotalPower]):
    area_item_bonus: int
    basic_card_total_power: int
    character_rank_bonus: int
    honor_bonus: int
    total_power: int

    def to_shared_model(self) -> SharedTotalPower:
        return SharedTotalPower(
            area_item_bonus=self.area_item_bonus,
            basic_card_total_power=self.basic_card_total_power,
            character_rank_bonus=self.character_rank_bonus,
            honor_bonus=self.honor_bonus,
            total_power=self.total_power,
        )


class User(BaseSchema):
    name: str
    rank: int
    user_id: int


class UserBondsHonor(BaseSchema):
    bonds_honor_id: int
    level: int


class UserCard(BaseSchema, ToSharedModel[Card]):
    card_id: int
    default_image: str
    level: int
    master_rank: int
    special_training_status: str

    def to_shared_model(self) -> Card:
        return Card(
            id=self.card_id,
            level=self.level,
            master_rank=self.master_rank,
            special_trained=self.special_training_status == "done",
        )


class UserChallengeLiveSoloResult(BaseSchema):
    character_id: int
    high_score: int


class UserChallengeLiveSoloStage(BaseSchema):
    character_id: int
    rank: int


class UserCharacter(BaseSchema):
    character_id: int
    character_rank: int


class UserConfig(BaseSchema):
    friend_request_scope: str


class UserCustomProfileCard(BaseSchema):
    # too complex XD
    pass


class UserDeck(BaseSchema):
    deck_id: int
    leader: int
    member1: int
    member2: int
    member3: int
    member4: int
    member5: int
    name: str
    sub_leader: int
    user_id: int


class UserHonorMission(BaseSchema):
    honor_mission_type: str
    progress: int


class UserHonor(BaseSchema):
    honor_id: int
    level: int


class UserMultiLiveTopScoreCount(BaseSchema):
    mvp: int
    super_star: int


class UserMusicDifficultyClearCount(BaseSchema):
    all_perfect: int
    full_combo: int
    live_clear: int
    music_difficulty_type: str


class UserProfile(BaseSchema):
    profile_image_type: str
    twitter_id: str
    user_id: int
    word: str


class UserProfileHonor(BaseSchema):
    bonds_honor_view_type: str
    bonds_honor_word_id: int
    honor_id: int
    honor_level: int
    profile_honor_type: str
    seq: int


class UserStoryFavorite(BaseSchema):
    pass


class Profile(BaseSchema):
    total_power: TotalPower
    user: User
    user_bonds_honors: list[UserBondsHonor]
    user_cards: list[UserCard]
    user_challenge_live_solo_result: UserChallengeLiveSoloResult
    user_challenge_live_solo_stages: list[UserChallengeLiveSoloStage]
    user_config: UserConfig
    user_custom_profile_cards: list[UserCustomProfileCard]
    user_deck: UserDeck
    user_honor_missions: list[UserHonorMission]
    user_honors: list[UserHonor]
    user_multi_live_top_score_count: UserMultiLiveTopScoreCount
    user_music_difficulty_clear_count: list[UserMusicDifficultyClearCount]
    user_profile: UserProfile
    user_profile_honors: list[UserProfileHonor]
    user_story_favorites: list[UserStoryFavorite]

    def to_user_info(self) -> UserInfo:
        profile = SharedProfile(
            name=self.user.name, bio=self.user_profile.word, twitter=self.user_profile.twitter_id
        )
        return UserInfo(
            id=self.user.user_id,
            rank=self.user.rank,
            profile=profile,
        )

    def to_deck(self) -> Deck:
        cards = [card.to_shared_model() for card in self.user_cards]
        members = tuple(
            iters.first(cards, lambda card: card.id == getattr(self.user_deck, f"member{i}"))
            for i in range(1, 6)
        )
        return Deck(
            id=self.user_deck.deck_id,
            name=self.user_deck.name,
            leader=members[0],
            subleader=members[1],
            members=cast(tuple[Card, Card, Card, Card, Card], members),
            total_power=self.total_power.to_shared_model(),
        )
