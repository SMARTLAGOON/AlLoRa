import builtins
from AlLoRa.utils.time_utils import get_current_timestamp

def print(*args, **kwargs):
    timestamp = get_current_timestamp()
    builtins.print(timestamp, *args, **kwargs)