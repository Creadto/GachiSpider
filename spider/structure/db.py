from abc import ABC, abstractmethod

class DocumentDB(ABC):
    @abstractmethod
    def create(self, *args, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def read(self, *args, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def find(self, *args, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def update(self, *args, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, *args, **kwargs):
        raise NotImplementedError

    