# Imports
import asyncio
import time
import nest_asyncio
from concurrent.futures import ThreadPoolExecutor

# Apply the patch at the start of your program
nest_asyncio.apply()

# Reference:
# https://pypi.org/project/nest-asyncio/

# Three requirements to define a function as aysnc and concurrency:
# Define function as async
# Pt the await keyword inside the function
# When calling it inside main(), schedule it with create_task()

"""
    Key differences:
    
    Async (Concurrency):
    One worker (CPU core) switching between tasks
    Good for I/O-bound tasks (waiting for data, network, etc.)
    Like one chef efficiently managing multiple dishes
    
    Parallelism:
    Multiple workers (CPU cores) working simultaneously
    Good for CPU-bound tasks (calculations, processing)
    Like multiple chefs each working on different dishes
    
"""

def MethodTwo():
    # Normal function
    print(f"{time.strftime('%H:%M:%S')} MethodTwo Starting")
    time.sleep(2.0)
    print(f"{time.strftime('%H:%M:%S')} MethodTwo Done")

async def MethodOne():
    print(f"{time.strftime('%H:%M:%S')} MethodOne Starting")
    await asyncio.sleep(2.5) # Already running asynch when you call this
    print(f"{time.strftime('%H:%M:%S')} MethodOne Done")

# Sequential version (one after another)
async def MainSequential():
    print(f"\n{time.strftime('%H:%M:%S')} Starting Sequential Test")
    with ThreadPoolExecutor() as pool:
        # This waits for MethodTwo to finish before starting MethodOne
        await asyncio.get_event_loop().run_in_executor(pool, MethodTwo)
        await MethodOne()

# Concurrent version (both running at same time) - Method 1 and Method 2
async def MainConcurrent():
    print(f"\n{time.strftime('%H:%M:%S')} Starting Concurrent Test")
    with ThreadPoolExecutor() as pool:
        # Start both methods without waiting
        task2 = asyncio.get_event_loop().run_in_executor(pool, MethodTwo)
        
        # if task 2 was defined with async and wait in the beginning, create task would be enough
        task1 = asyncio.create_task(MethodOne())
        
        # Wait for both to complete
        await task2
        await task1

if __name__ == "__main__":
    # Run both versions to see the difference
    asyncio.run(MainSequential())
    asyncio.run(MainConcurrent())
