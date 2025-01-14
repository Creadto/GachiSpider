from bs4 import BeautifulSoup as bs
from spider.structure import Node, State
from spider.utils.io import get_form
from spider.utils.web import clean_text
from .store import StoreLocal
from .failed import Failed

class Parse(State):
    def __init__(self, node: Node, parent):
        super(Parse, self).__init__("parse", node=node, parent=parent)
        form_dict = get_form(node=self.node, logger=self.logger)
        self.node = form_dict['node']
        self.form = form_dict['form']
        if self.form is None:
            self.node.label = "Not found correct form"
            self.parent.transit(Failed(node=self.node, parent=self.parent))
        
    def run(self):
        try:
            self.node.data = self._parse()
            # If It's a text only post without media files, Move through RDB(Be the Frozen immediately)
            n_media = 0
            if "images" in self.node.data:
                n_media += len(self.node.data['images'])
            
            if "videos" in self.node.data:
                n_media += len(self.node.data['videos'])
            
            if n_media == 0:
                self.node.cache = None
                self.node.freshness = -1
                self.node.label = "Frozen"
            
            self.parent.transit(StoreLocal(node=self.node, parent=self.parent, root='/tmp/datalake/red_zone'))
        except Exception as e:
            import traceback
            self.node.label = "Not found correct form"
            self.logger.error(traceback.print_exc())
            self.parent.transit(Failed(node=self.node, parent=self.parent))
            
    def pause(self):
        raise NotImplementedError
    
    def stop(self):
        raise NotImplementedError
    
    def _get_attrs(self, handle, method, args):
        if isinstance(args, str):
            return getattr(handle, method)(args)
        elif isinstance(args, list):
            return getattr(handle, method)(*args)
        elif isinstance(args, dict):
            return getattr(handle, method)(**args)
        else:
            raise KeyError
        
    def _parse(self):
        gathered = dict()
        soup = bs(self.node.cache, 'html.parser')
        for tag, value in self.form.items():
            self.logger.info(tag)
            result = self._get_attrs(soup, value['method'], value['tag'])
                         
            if 'attrs' in value:
                attrs = value['attrs']
                for i, stub in reversed(list(enumerate(result))):
                    if attrs is None:
                        cond = not bool(stub.attrs)
                    else:
                        cond = attrs[0] in stub.attrs and stub.attrs[attrs[0]] == attrs[1]
                    
                    if cond is False:
                        del result[i]
                    else:
                        self.logger.debug(result[i])
            
            if 'html' in value and value['html']:
                gathered[tag] = [{'text': stub.prettify(), 'attrs': None} for stub in result]
            else:
                tag_opt = True
                if 'withTag' in value:
                    tag_opt = value['withTag']
                
                chunk = [{'text': clean_text(stub, tag_opt), 'attrs': stub.attrs} for stub in result]
                gathered[tag] = [segment for segment in chunk if segment['text'] != ""]

        return gathered
    
