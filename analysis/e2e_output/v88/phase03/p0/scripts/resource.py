# Mock resource module for Windows compatibility
class _Usage:
    def __init__(self, maxrss):
        self.ru_maxrss = maxrss

def getrusage(who):
    """Return fake usage with ru_maxrss in KB."""
    # Try psutil for real value, else return 0
    try:
        import psutil
        proc = psutil.Process()
        rss_kb = proc.memory_info().rss // 1024
    except:
        rss_kb = 0
    return _Usage(rss_kb)
