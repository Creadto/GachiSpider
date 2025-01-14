import json
import os
from typing import List
from spider.structure import Node, State
from bs4 import BeautifulSoup

from spider.utils.web import clean_text
from .succeeded import Succeeded
from .failed import Failed


class Format(State):
    def __init__(self, node: Node, parent):
        super(Format, self).__init__("format", node=node, parent=parent)
        self.form = self._get_form()
        self.body = ""
        if self.form is not None:
            t_mark = '\t' * self.form['depth']
            for pre in self.form['head']:
                self.body += t_mark + pre
                
    def _get_form(self):
        root = "./spider/form"
        file_path = os.path.join(root, "gachiga.com", 'index.json') 
        if not os.path.exists(file_path):
            self.logger.warning("Not found %s" % file_path)
            return None
        
        with open (file_path, "r") as f:
            form = json.load(f)
        return form
    
    def _make_element(self, contents, kind: str):
        depth = self.form['body']['depth']
        t_mark = '\t' * depth
        sub_form = self.form['body'][kind]
        
        body = t_mark + sub_form['pre'] + contents + sub_form['post']
        return body
    
    def _find_index(self, value: str, alternatives: List[str]):
        for i, alter in enumerate(alternatives):
            if value == alter:
                return i
        return None
    
    def _make_body(self):
        data = self.node.data
        cache = self.node.cache
        urls = cache['urls']
        contents = [content['text'] for content in data['contents']]
        storage_paths = cache['storage_paths']

        html = data['html'][-1]['text']
        soup = BeautifulSoup(html, 'html.parser')
        
        for element in soup.find_all(True):
            keys = [key for key in element.attrs.keys() if 'src' in key]
            if len(keys) != 0:
                index = self._find_index(element.attrs[keys[0]], urls)
                if index != None:  
                    saved_path = storage_paths[index]
                    if saved_path is not None:
                        self.body += self._make_element(saved_path, "images")
            else:
                cleaned_text = clean_text(element)
                if cleaned_text != "":
                    index = self._find_index(cleaned_text, contents)
                    self.body += self._make_element(contents[index], "texts")
        
        t_mark = '\t' * self.form['depth']
        for post in self.form['tail']:
            self.body += t_mark + post
        
        return self.body
    
    def run(self):
        try:
            self.node.cache = self._make_body()
            self.node.label = "Transformed"
            self.parent.transit(Succeeded(node=self.node, parent=self.parent))
        except Exception as e:
            self.node.label = "Failed Formatting"
            self.parent.transit(Failed(node=self.node, parent=self.parent))
        
    def pause(self):
        pass
    
    def stop(self):
        pass
    