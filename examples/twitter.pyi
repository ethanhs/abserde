from typing import List, Optional, Any, Union
from abserde import abserde


@abserde
class SearchMetadata:
    completed_in: float
    max_id: float
    max_id_str: str
    next_results: str
    query: str
    refresh_url: str
    count: int
    since_id: int
    since_id_str: str


@abserde
class Hashtag:
    text: str
    indices: List[int]


@abserde
class Size:
    w: int
    h: int
    resize: str


@abserde
class Sizes:
    medium: Size
    small: Size
    thumb: Size
    large: Size


@abserde
class Media:
    id: float
    id_str: str
    indices: List[int]
    media_url: str
    media_url_https: str
    url: str
    display_url: str
    expanded_url: str
    typ: str
    sizes: Sizes
    source_status_id: Optional[float]
    source_status_id_str: Optional[str]


@abserde
class URL:
    url: str
    expanded_url: str
    display_url: str
    indices: List[int]


@abserde
class UserMention:
    screen_name: str
    name: str
    id: int
    id_str: str
    indices: List[int]


@abserde
class StatusEntities:
    hashtags: List[Hashtag]
    symbols: List[Any]
    urls: List[URL]
    user_mentions: List[UserMention]
    media: Optional[List[Media]]


@abserde
class Metadata:
    result_type: str
    iso_language_code: str


@abserde
class Description:
    urls: List[URL]


@abserde
class UserEntities:
    description: Description
    url: Optional[Description]


@abserde
class User:
    id: int
    id_str: str
    name: str
    screen_name: str
    location: str
    description: str
    entities: UserEntities
    protected: bool
    followers_count: int
    friends_count: int
    listed_count: int
    created_at: str
    favourites_count: int
    geo_enabled: bool
    verified: bool
    statuses_count: int
    lang: str
    contributors_enabled: bool
    is_translator: bool
    is_translation_enabled: bool
    profile_background_color: str
    profile_background_image_url: str
    profile_background_image_url_https: str
    profile_background_tile: bool
    profile_image_url: str
    profile_image_url_https: str
    profile_link_color: str
    profile_sidebar_border_color: str
    profile_sidebar_fill_color: str
    profile_text_color: str
    profile_use_background_image: bool
    default_profile: bool
    default_profile_image: bool
    following: bool
    follow_request_sent: bool
    notifications: bool
    url: Optional[str]
    utc_offset: Optional[int]
    time_zone: Optional[str]
    profile_banner_url: Optional[str]

@abserde
class InnerStatus:
    metadata: Metadata
    created_at: str
    id: float
    id_str: str
    text: str
    source: str
    truncated: bool
    user: User
    geo: Optional[Any]
    coordinates: Optional[Any]
    place: Optional[Any]
    contributors: Optional[Any]
    retweet_count: int
    favorite_count: int
    entities: StatusEntities
    favorited: bool
    retweeted: bool
    lang: str
    in_reply_to_status_id: Optional[float]
    in_reply_to_status_id_str: Optional[str]
    in_reply_to_user_id: Optional[int]
    in_reply_to_user_id_str: Optional[str]
    in_reply_to_screen_name: Optional[str]
    possibly_sensitive: Optional[bool]

@abserde
class Status:
    metadata: Metadata
    created_at: str
    id: float
    id_str: str
    text: str
    source: str
    truncated: bool
    user: User
    geo: Optional[Any]
    coordinates: Optional[Any]
    place: Optional[Any]
    contributors: Optional[Any]
    retweet_count: int
    favorite_count: int
    entities: StatusEntities
    favorited: bool
    retweeted: bool
    lang: str
    in_reply_to_status_id: Optional[float]
    in_reply_to_status_id_str: Optional[str]
    in_reply_to_user_id: Optional[int]
    in_reply_to_user_id_str: Optional[str]
    in_reply_to_screen_name: Optional[str]
    retweeted_status: Optional[InnerStatus]
    possibly_sensitive: Optional[bool]


@abserde
class File:
    statuses: List[Status]
    search_metadata: SearchMetadata
