import win32evtlog
import win32con

def debug_windows_logs():
    print("Reading last 5 Error/Warning events from System log...")
    try:
        log_handle = win32evtlog.OpenEventLog(None, "System")
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEEK_READ
        total_records = win32evtlog.GetNumberOfEventLogRecords(log_handle)
        offset = total_records - 1
        
        count = 0
        while count < 5 and offset >= 0:
            events = win32evtlog.ReadEventLog(log_handle, flags, offset)
            for event in events:
                if event.EventType in (win32con.EVENTLOG_ERROR_TYPE, win32con.EVENTLOG_WARNING_TYPE):
                    print(f"\n--- Event {count+1} ---")
                    print(f"Source: {event.SourceName}")
                    print(f"Time: {event.TimeGenerated}")
                    print(f"ID: {event.EventID}")
                    print(f"StringData type: {type(event.StringData)}")
                    print(f"StringData content: {event.StringData}")
                    
                    data_raw = getattr(event, "Data", "N/A")
                    print(f"Data raw: {data_raw}")
                    
                    count += 1
                    if count >= 5: break
                offset -= 1
            if not events: break
        win32evtlog.CloseEventLog(log_handle)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_windows_logs()
