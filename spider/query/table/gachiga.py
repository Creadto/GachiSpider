from dataclasses import dataclass
from spider.structure import Entity

@dataclass
class Post(Entity):
    author_id: int = 0
    title: str = ""
    content: str = ""
    thumbnail_photo_url: str = None
    category: str = ""
    country_code_bitmask: int = 0
    country_code: str = ""
    view_count: int = 0
    entity_status: str = ""
    state_code: str = ""
    city_code: str = ""
    created_date_time: str = ""
    last_modified_date_time: str = ""
    dtype: str = ""

@dataclass
class News(Entity):
    post_id: int = 0
    sub_category: str = ""
    like_count: int = 0
    comment_count: int = 0
    content_grade: str = "NORMAL"

@dataclass
class Bulletin(Entity):
    post_id: int = 0
    like_count: int = 0
    comment_count: int = 0
    content_grade: str = "NORMAL"

def get_region_code(region: str):
    region = region.upper()
    alternatives = [
        "UNI",
        "KR", "US", "JP", "CN", "VN", "SG",
        "TH", "PH", "MY", "ID", "GU", "AU",
        "UZ", "CA", "RU", "LA", "GB", "DE",
        "BR", "NZ", "FR", "AR", "UA", "KZ"
    ]
    region_map = dict()
    total_value = 0
    for i, key in enumerate(alternatives):
        region_map[key] = 1 << i
        total_value += region_map[key]
    
    region_map["UNIVERSAL"] = total_value
    
    return None if region not in region_map else region_map[region]