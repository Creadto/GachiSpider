import copy
from spider.query.table.gachiga import Post, News, Bulletin, get_region_code
from spider.structure import Node
from spider.structure.data import Entity
from spider.utils.io import get_json
from .base import Handler

class GachiGaHandler(Handler):
    def __init__(self, **kwargs):
        super(GachiGaHandler, self).__init__(**kwargs)
        config_root = "./spider/configs"
        self.root_nodes = get_json(config_root, "root nodes.json")
        self._meta_data = {"author_id": 867, "view_count": 0, "created_date_time": self.created_time, "last_modified_date_time": self.created_time, "entity_status": "ACTIVE", "sub_category": "", "like_count": 0, "comment_count": 0}

    def run(self, node: Node):
        root_url = node.fan_in[0]
        meta_data = copy.deepcopy(self._meta_data)
        meta_data['content'] = node.cache
        meta_data['title'] = node.data['title'][-1]['text']
        if len(node.data['images']) > 0:
            meta_data['thumbnail_photo_url'] = node.data['images'][0]['saved_path']
        info = {'post': Post()}        
        if root_url in self.root_nodes:
            root_meta = self.root_nodes[root_url]
            stub = {
                'country_code': get_region_code(root_meta["region"]),
                'category': root_meta['kind'].upper(),
                'dtype': root_meta['kind'].lower()
            }
            if 'subtitle' in root_meta:
                stub['sub_category'] = root_meta["subtitle"]
                info['news'] = News()
            else:
                info['bulletin'] = Bulletin()

            meta_data.update(stub)
            
            for key, value in info.items():
                value.update(meta_data)
                meta_data['post_id'] = self._insert_data(key, value)
            
            node.label = "Frozen"
            node.freshness = -1
            return node
        else:
            return node
    
    def _insert_data(self, table_name: str, entity: Entity) -> int:
        post_id = -1
        with self.db_client.cursor() as cursor:
            query = self._make_query(table_name, entity)
            cursor.execute(query)
            post_id = cursor.lastrowid
            self.db_client.commit()
        
        return post_id
            
    def _make_query(self, table_name: str, entity: Entity):
        entity_dict = entity.to_dict()
        columns = ", ".join(f"`{key}`" for key in entity_dict.keys())  # Add backticks for column names
        values = ", ".join(
            "NULL" if value is None else f"'{value}'" if isinstance(value, str) else str(value)
            for value in entity_dict.values()
            )
        query = f"INSERT INTO `{table_name}` ({columns}) VALUES ({values});"
        return query