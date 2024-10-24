try:
    # For regular Python
    import time
    from time import strftime

    def get_current_timestamp():
        return time.strftime("[%Y-%m-%d %H:%M:%S]")

    def get_time():
        return get_current_timestamp()

    def current_time_ms():
        return int(time.time() * 1000)  # Time in milliseconds

    def sleep(seconds):
        time.sleep(seconds)

    def sleep_ms(milliseconds):
        time.sleep(milliseconds / 1000.0)

    def save_time():
        pass

except ImportError:
    # For MicroPython
    import utime as time
    import machine
    from ujson import loads, dumps

    def update_time():
        try:
            rtc = machine.RTC()

            # Check if RTC is already set (you can implement a check based on your needs)
            if rtc.datetime()[0] == 2000:
                # Try loading RTC data from file
                try:
                    with open("datetime.json", "r") as f:
                        rtc_data = loads(f.read())
                except:
                    rtc_data = {
                                    "year": 2024,
                                    "month": 11,
                                    "day": 6,
                                    "weekday": 2,
                                    "hour": 12,
                                    "minute": 00,
                                    "second": 0
                                }
                # Set RTC manually
                rtc.datetime((rtc_data.get("year"), rtc_data.get("month"), rtc_data.get("day"), rtc_data.get("weekday"), rtc_data.get("hour"), rtc_data.get("minute"), rtc_data.get("second"), 0))
        except:
            pass

    # Ensure RTC is set at startup
    update_time()

    def get_current_timestamp():
        tt = time.localtime()
        return "[{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}]".format(*tt[:6])

    def get_time():
        return get_current_timestamp()

    def current_time_ms():
        return time.ticks_ms()  # Time in milliseconds

    def sleep(seconds):
        time.sleep(seconds)

    def sleep_ms(milliseconds):
        time.sleep_ms(milliseconds)

    def save_time():
        try:
            rtc = machine.RTC()
            rtc_data = {
                "year": rtc.datetime()[0],
                "month": rtc.datetime()[1],
                "day": rtc.datetime()[2],
                "weekday": rtc.datetime()[3],
                "hour": rtc.datetime()[4],
                "minute": rtc.datetime()[5],
                "second": rtc.datetime()[6]
            }
            with open("datetime.json", "w") as f:
                f.write(dumps(rtc_data))

        except:
            pass