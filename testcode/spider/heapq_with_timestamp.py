"""
    Title: Heapq, How to use more efficiently(Data object with Timestamp)
    Description: This code is a test code for heapq.
    Features:
    - Heapq is used to manage data objects with timestamps.
    - Amazingly, the heapq module can be used to manage data objects with timestamps!
"""
import heapq
from collections import deque
from datetime import datetime, timedelta

MAX_LENGTH = 5
time_heap = deque(maxlen=MAX_LENGTH)

now = datetime.now()
time_entries = [
    (now - timedelta(seconds=5), "Event A"),
    (now - timedelta(seconds=10), "Event B"),
    (now, "Event C"),
    (now - timedelta(seconds=2), "Event D"),
    (now - timedelta(seconds=8), "Event E"),
    (now - timedelta(seconds=15), "Event F"),
]

def push_to_heap(heap, item):
    heapq.heappush(heap, item)  
    if len(heap) > heap.maxlen:  
        heapq.heappop(heap)


for entry in time_entries:
    push_to_heap(time_heap, entry)

print("Heap contents (limited by max length):")
for t, metadata in time_heap:
    print(f"{t} - {metadata}")

print("\nPopping items from heap (oldest first):")

while time_heap:
    oldest_entry = heapq.heappop(time_heap)
    time_value, metadata = oldest_entry
    print(f"{time_value} - {metadata}")
