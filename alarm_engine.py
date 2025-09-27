
import json, time, threading, os
from datetime import datetime, timedelta
from notify_utils import show_task_popup, notify
from settings import load_settings

def _parse_time_str(s):
    return datetime.strptime(s.strip(), "%H:%M").time()

def _parse_range_to_timestr(time_range):
    start_str, end_str = time_range.split("-")
    return start_str.strip(), end_str.strip()

def _today_dt(hhmm):
    today = datetime.today().date()
    return datetime.strptime(f"{today} {hhmm}", "%Y-%m-%d %H:%M")

def _duration_minutes(time_range):
    try:
        s, e = _parse_range_to_timestr(time_range)
        return int((_today_dt(e) - _today_dt(s)).total_seconds() // 60)
    except Exception:
        return 60

def _save_progress(name, status):
    cfg = load_settings()
    if not cfg.get("save_progress", True):
        return
    entry = {"task": name, "status": status, "timestamp": datetime.now().isoformat(timespec="seconds")}
    try:
        if os.path.exists("progress.json"):
            with open("progress.json","r",encoding="utf-8") as f:
                arr = json.load(f)
        else:
            arr = []
        arr.append(entry)
        with open("progress.json","w",encoding="utf-8") as f:
            json.dump(arr,f,ensure_ascii=False,indent=2)
    except Exception:
        pass

def _reminder_loop(stop_event):
    cfg = load_settings()
    interval = int(cfg.get("reminder_interval_min", 120))
    if interval < 15: interval = 15
    while not stop_event.is_set():
        time.sleep(interval * 60)
        if stop_event.is_set(): break
        if load_settings().get("daily_ai_reminders", True):
            notify("Daily Reminder", "Take a mindful breath. Review your next block in schedule.json.")

def start_alarm_loop(schedule_path="schedule.json", poll_seconds=30):
    cfg = load_settings()
    stop_event = threading.Event()
    if cfg.get("daily_ai_reminders", True):
        threading.Thread(target=_reminder_loop, args=(stop_event,), daemon=True).start()

    with open(schedule_path, "r", encoding="utf-8") as f:
        schedule = json.load(f)

    notified = set()
    block_times = {b["block"]: b["time"] for b in schedule.get("tasks", [])}

    while True:
        now_t = datetime.now().time()
        for block in schedule.get("tasks", []):
            name = block["block"]
            tasks = block.get("tasks", [])
            if name in notified:
                continue

            time_range = block_times.get(name, block["time"])
            start_str, end_str = _parse_range_to_timestr(time_range)
            try:
                start_t = _parse_time_str(start_str)
                end_t = _parse_time_str(end_str)
            except Exception:
                continue

            if datetime.now().time() > end_t and cfg.get("auto_reroll_missed", True):
                dur = _duration_minutes(time_range)
                new_start_dt = datetime.now() + timedelta(minutes=1)
                new_end_dt = new_start_dt + timedelta(minutes=dur)
                block_times[name] = f"{new_start_dt.strftime('%H:%M')}-{new_end_dt.strftime('%H:%M')}"
                continue

            if now_t >= start_t:
                action, new_time = show_task_popup(name, tasks, time_range)
                if action == "reschedule" and new_time:
                    block_times[name] = new_time
                elif action == "next":
                    _save_progress(name, "completed")
                    notified.add(name)
                elif action == "stop":
                    _save_progress(name, "stopped")
                    stop_event.set()
                    return
        time.sleep(poll_seconds)
