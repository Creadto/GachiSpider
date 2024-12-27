from abc import ABC, abstractmethod
import logging
from .engine import Engine

# DDD에 따라서 도메인 함수들을 정의하는 클래스
# 다만 기본적인 Scheduler 기능들은 abstract method로 정의되어 있음
class Scheduler(ABC):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):         
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, *args, **kwargs):
        """
        Initializes the scheduler with an instance of Engine.

        Parameters:
        *args: Positional arguments for Engine.
        **kwargs: Keyword arguments for Engine.
        Returns:
        Scheduler: An base instance of Scheduler.
        """
        self._base_logger = logging.getLogger(name="Scheduler")
        self._engine = Engine(*args, **kwargs)
    
    @abstractmethod
    def add_request(self, request):
        pass

    @abstractmethod
    def get_request(self):
        pass
    
    @abstractmethod
    def task_done(self):
        pass

    @abstractmethod
    def join(self):
        pass
    
    @abstractmethod
    def empty(self):
        pass
