import os
from typing import Dict
import uuid
from datetime import datetime

import boto3
from spider.structure import Node, State
from spider.utils.web import download_media
from .format import Format
from .failed import Failed


class Collect(State):
    def __init__(self, node: Node, parent):
        super(Collect, self).__init__("collect", node=node, parent=parent)
        self.save_root = "/tmp/"
        self.bucket_name = "gachiga"
        self.s3_client = boto3.client(service_name="s3", region_name="ap-northeast-2")
        self.bridge_directory = datetime.today().strftime("%Y/%m/%d")
    
    def __get_paths(self, category, url) -> Dict[str, str]:
        filename = str(uuid.uuid1())
        file_root = os.path.join(self.save_root, category, self.bridge_directory, filename)
        storage_root = os.path.join(category, self.bridge_directory, filename)
        if os.path.exists(file_root) == False:
            self.logger.info("%s, make dirs" % (file_root))
            os.makedirs(file_root)
        
        if category == "images":
            if ".gif" in url:
                filename += ".gif"
            else:
                filename += ".jpg"
        elif category == "videos":
            filename += ".mp4"
        else:
            self.logger.warning("Unrecognized file format")
            return None
        
        result = {
            'local_path': os.path.join(file_root, filename),
            'storage_path': os.path.join(storage_root, filename),
            'url': url,
            "filename": filename
        }
        return result
        
    def __download(self, url, local_path, **kwargs) -> str:
        saved_path = download_media(url=url, save_path=local_path)
        if saved_path == None:
            raise RuntimeError
        
        return saved_path
    
    def __upload(self, local_path, storage_path, **kwargs) -> str:
        self.s3_client.upload_file(local_path, self.bucket_name, storage_path)
        return storage_path
      
    def run(self):
        self.node.cache = {'urls': [], 'tmp_paths': [], 'storage_paths': []}
        data = self.node.data
        self.logger.info("Check media files in %s" % self.node.url)     
        for category, contents in data.items():
            for i, content in enumerate(contents):
                if 'attrs' in content and content['attrs'] != None:
                    keys = [key for key in content['attrs'].keys() if 'src' in key]
                    if len(keys) == 0:
                        continue
                    
                    paths = self.__get_paths(category=category, url=content['attrs'][keys[0]])
                    if paths == None:
                        continue
                    
                    try:       
                        self.logger.info("Request %s source from %s" % (category, paths['url']))
                        saved_path = self.__download(**paths)
                        self.logger.info("Media source downloaded, saved to %s" % saved_path)
                        saved_path = self.__upload(**paths)
                        self.logger.info("Media uploaded successfully to %s" % saved_path)
                        self.node.data[category][i]["saved_path"] = saved_path
                        
                        self.node.cache['urls'].append(paths['url'])
                        self.node.cache['tmp_paths'].append(paths['local_path'])
                        self.node.cache['storage_paths'].append(paths['storage_path'])
                    except RuntimeError:
                        self.logger.error("Failed download file(%s)" % (paths['url']))
                        self.node.label = "Download failed"
                        self.parent.transit(Failed(node=self.node, parent=self.parent))
                        return
                    except ConnectionError:
                        self.logger.error("Failed upload to %s" % (paths['storage_path']))
                        self.node.label = "Upload failed"
                        self.parent.transit(Failed(node=self.node, parent=self.parent))
                    except Exception as e:
                        self.logger.error("Unrecognized error")
                        self.parent.transit(Failed(node=self.node, parent=self.parent))
                        
        self.node.label = "Saved contents into S3"
        self.parent.transit(Format(node=self.node, parent=self.parent))
    
    def pause(self):
        pass
    
    def stop(self):
        pass
    