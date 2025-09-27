
from plyer import notification
import pygame
import tkinter as tk
from tkinter import StringVar
import threading, time
from datetime import datetime, timedelta

try:
    pygame.mixer.init()
except Exception:
    pass

def notify(title, message):
    try:
        notification.notify(title=title, message=message, app_name="AI Scheduler", timeout=10)
    except Exception:
        pass

def play_alarm_loop(sound_path="sounds/alert.wav"):
    try:
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play(-1)
    except Exception:
        pass

def stop_alarm():
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass

def show_task_popup(block_name, tasks, current_time_range):
    result = {"action": None, "new_time": None}
    stop_flag = {"value": False}

    def on_next():
        result["action"] = "next"
        stop_alarm()
        stop_flag["value"] = True
        root.destroy()

    def on_stop():
        result["action"] = "stop"
        stop_alarm()
        stop_flag["value"] = True
        root.destroy()

    def on_change_time():
        result["action"] = "reschedule"
        new_start = start_entry.get().strip()
        new_end = end_entry.get().strip()
        result["new_time"] = f"{new_start}-{new_end}"
        stop_alarm()
        stop_flag["value"] = True
        root.destroy()

    try:
        start_str, end_str = current_time_range.split("-")
        today = datetime.today().date()
        end_time = datetime.strptime(f"{today} {end_str}", "%Y-%m-%d %H:%M")
    except Exception:
        end_time = datetime.now() + timedelta(hours=1)

    notify(f"⏰ {block_name} Started", "\n".join(tasks))
    play_alarm_loop()

    root = tk.Tk()
    root.title(f"{block_name} Block")
    root.geometry("560x560")
    root.configure(bg="#f7f7f7")

    tk.Label(root, text=f"⏰ {block_name} Block", font=("Segoe UI", 16, "bold"), bg="#f7f7f7").pack(pady=10)
    frame_tasks = tk.Frame(root, bg="#f7f7f7"); frame_tasks.pack()
    for t in tasks:
        tk.Label(frame_tasks, text=f"• {t}", font=("Segoe UI", 12), anchor="w", bg="#f7f7f7").pack(pady=2, anchor="w")

    tk.Label(root, text=f"Time: {current_time_range}", font=("Segoe UI", 11), bg="#f7f7f7").pack(pady=6)

    timer_var = StringVar(value="00:00:00")
    lab = tk.Label(root, textvariable=timer_var, font=("Consolas", 28, "bold"), fg="#d32f2f", bg="#f7f7f7")
    lab.pack(pady=6)

    def update_timer():
        while not stop_flag["value"]:
            now = datetime.now()
            rem = end_time - now
            if rem.total_seconds() <= 0:
                timer_var.set("00:00:00")
                break
            h = int(rem.total_seconds() // 3600)
            m = int((rem.total_seconds() % 3600) // 60)
            s = int(rem.total_seconds() % 60)
            timer_var.set(f"{h:02d}:{m:02d}:{s:02d}")
            time.sleep(1)

    threading.Thread(target=update_timer, daemon=True).start()

    pane = tk.Frame(root, bg="#f7f7f7"); pane.pack(pady=10)
    tk.Label(pane, text="Start (HH:MM):", bg="#f7f7f7").grid(row=0, column=0, padx=4, pady=3)
    start_entry = tk.Entry(pane, width=8); start_entry.grid(row=0, column=1, padx=4, pady=3)
    start_entry.insert(0, current_time_range.split("-")[0])

    tk.Label(pane, text="End (HH:MM):", bg="#f7f7f7").grid(row=1, column=0, padx=4, pady=3)
    end_entry = tk.Entry(pane, width=8); end_entry.grid(row=1, column=1, padx=4, pady=3)
    end_entry.insert(0, current_time_range.split("-")[1])

    bar = tk.Frame(root, bg="#f7f7f7"); bar.pack(pady=12)
    tk.Button(bar, text="NEXT TASK", command=on_next, width=12, bg="#2e7d32", fg="white").grid(row=0, column=0, padx=6)
    tk.Button(bar, text="STOP", command=on_stop, width=10, bg="#c62828", fg="white").grid(row=0, column=1, padx=6)
    tk.Button(bar, text="CHANGE TIME", command=on_change_time, width=14, bg="#1565c0", fg="white").grid(row=0, column=2, padx=6)

    root.mainloop()
    return result["action"], result["new_time"]
