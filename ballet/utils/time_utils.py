from typing import Callable, Tuple, TypeVar, Optional
import time
import statistics

A = TypeVar('A')
B = TypeVar('B')


def timeit(f: Callable[[A], B], n: Optional[int]=1) -> Tuple[B, float]: 
    begin = time.now
    res = f()
    for _ in range(n-1):
        f()
    end = time.now
    fulltime = end - begin
    return res, fulltime / n

def timeit_detailed(f: Callable[[A], B], n: Optional[int]=1) -> Tuple[B, dict[str, float]]: 
    times = []
    for _ in range(n):
        begin = time.time()
        res = f()
        end = time.time()
        fulltime = end - begin
        times.append(fulltime)
        
    if times:
        mean_time = statistics.mean(times)
        variance_time = statistics.variance(times) if len(times) > 1 else 0.0
        stdev_time = statistics.stdev(times) if len(times) > 1 else 0.0
        median_time = statistics.median(times)
        q1_time = statistics.quantiles(times, n=4)[0]
        q3_time = statistics.quantiles(times, n=4)[2]
    else:
        mean_time = variance_time = stdev_time = median_time = q1_time = q3_time = 0.0
        
    stats = {
        "mean": mean_time,
        "variance": variance_time,
        "stdev": stdev_time,
        "median": median_time,
        "q1": q1_time,
        "q3": q3_time
    }
    return res, stats