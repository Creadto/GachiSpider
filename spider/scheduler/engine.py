import time
import heapq
import logging
import threading
from datetime import datetime
from typing import Dict


class Engine:
    def __init__(self, period=0.3, result_length=5000, name="engine"):
        # 큐 길이 이상으로 계속 쌓이면 heapq 특성상 최신 것들이 삭제됨
        # 이는 철학적 차이인데, 오래된 것을 체크하지 않았기에 최신 것을 쌓지 않겠다는 마음임
        self.logger = logging.getLogger(name=name)
        self.active = False
        self.base_period = period
        self.fixed_results = []
        self.max_length = result_length
        
        self._main_events = dict()
        self._single_events = []
        self._fixed_events = dict()

        self.timer = threading.Timer(self.base_period, self.fixed_update)
    
    def __contains__(self, key):
        cond1 = key in self._main_events
        cond2 = key in self._fixed_events
        alters = [True for _, name, _, _ in self._single_events if key == name]
        cond3 = len(alters) > 0
        return cond1 | cond2 | cond3
    
    def update(self):
        result = dict()
        if self.active == False:
            return result
        
        for name, pair in self._main_events.items():
            event, kwargs = pair
            result["[MAIN]" + name] = event(**kwargs)
        
        while len(self._single_events) > 0:
            tup = self._single_events.pop(0)
            event, name, delay, kwargs = tup
            trigger_time = delay - time.time()
            if trigger_time > 0:
                self._single_events.append(tup)
                continue
            else:
                result["[SINGLE]"+ name] = event(**kwargs)
            
        return result
    
    def fixed_update(self):
        begin = time.time()
        result = dict()
        if self.active == False:
            return
        
        for name, tup in self._fixed_events.items():
            event, kwargs, period, cum_seconds = tup
            cum_seconds += self.base_period
            if cum_seconds < period:
                self._fixed_events[name] = (event, kwargs, period, cum_seconds)
                continue
            else:
                self._fixed_events[name] = (event, kwargs, period, 0)
                result["[PERIODIC]" + name] = event(**kwargs)
        
        if len(result) > 0:
            heapq.heappush(self.fixed_results, (datetime.now(), result))
            if len(self.fixed_results) > self.max_length:
                heapq.heappop(self.fixed_results)
        
        if time.time() - begin > self.base_period:
            self.base_period = time.time() - begin
        self.timer = threading.Timer(self.base_period, self.fixed_update)
        self.timer.start()
            
    def run(self)->Dict[str, object]:
        if self.timer.is_alive() == False:
            self.active = True
            self.timer.start()
        return self.update()
    
    def stop(self)->Dict[str, object]:
        self.active = False
        self.timer.cancel()
        return dict()
    
    def add_event(self, event, name, **kwargs):
        if name in self._main_events or name in self._fixed_events:
            return None
        self._main_events[name] = (event, kwargs)
        return len(self._main_events)
    
    def add_single_event(self, event, name, delay=0, **kwargs):
        # In cases of single event, it can use duplicated name
        self._single_events.append((event, name, time.time() + delay, kwargs))
        return len(self._single_events)
        
    def add_fixed_event(self, event, name, period, **kwargs):
        if name in self._main_events or name in self._fixed_events:
            return None
        self._fixed_events[name] = (event, kwargs, period, period)
        return len(self._fixed_events)
    
    def del_event(self, name):
        if name in self._main_events:
            del self._main_events[name]
            
        if name in self._fixed_events:
            del self._fixed_events[name]
            
        while len(self._single_events) > 0:
            tup = self._single_events.pop(0)
            _, event_name, _, _ = tup
            
            if name != event_name:
                self._single_events.append(tup)
