from spider.structure import Node, State


class Succeeded(State):
    def __init__(self, node: Node, parent):
        super(Succeeded, self).__init__("succeeded", node=node, parent=parent, label_pass=True)
        
    def run(self):
        pass
    
    def pause(self):
        pass
    
    def stop(self):
        pass
    