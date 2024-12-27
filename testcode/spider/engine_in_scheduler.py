""" 
    Title: Test code for Engine in Scheduler
    Description: This code is a test code for Engine in Scheduler.
    Features:
    - There are at least several fixed events, and each is executed without parallelism.
    - Each reserved event is triggered after the 'run' method is executed.
    - The 'stop' method does not handle the process of clearing all events.
    - The results from fixed events are sorted based on their timestamps.
"""
import time
from spider.scheduler.engine import Engine

def print_hello(x: int, message: str="Hello"):
    for i in range(x):
        print("%s-%d" % (message, i))

def main():
    engine = Engine(period=1)
    engine.add_fixed_event(print_hello, "print_hello", x=10, message="Hi")
    time.sleep(5)
    engine.run()
    time.sleep(3)
    engine.add_fixed_event(print_hello, "print_hello_post", x=10, message="Post-Hi")
    
    for i in range(10):
        print("Main-%d" % (i))
        time.sleep(1.2)
    
    engine.del_event("print_hello")
    engine.stop()

if __name__ == "__main__":
    main()