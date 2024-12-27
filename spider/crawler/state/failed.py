from spider.structure import Node, State


class Failed(State):
    def __init__(self, node: Node, parent):
        super(Failed, self).__init__("failed", node=node, parent=parent, label_pass=True)
        
    def run(self):
        pass
    
    def pause(self):
        pass
    
    def stop(self):
        pass
    