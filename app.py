
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json, os, threading, platform, subprocess
from settings import load_settings, save_settings
from goal_parser import generate_schedule
from alarm_engine import start_alarm_loop

def open_folder(path="."):
    if platform.system()=="Windows":
        os.startfile(os.path.abspath(path))
    elif platform.system()=="Darwin":
        subprocess.call(["open", os.path.abspath(path)])
    else:
        subprocess.call(["xdg-open", os.path.abspath(path)])

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Scheduler — Personal Power Mode")
        self.geometry("900x720")
        self.configure(bg="#f7f7f7")
        self.settings = load_settings()
        self._build_ui()

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        # Generate Schedule
        frm_gen = ttk.Frame(nb); nb.add(frm_gen, text="Generate Schedule")
        tk.Label(frm_gen,text="Custom Instructions / Context",font=("Segoe UI",11,"bold")).grid(row=0,column=0,sticky="w",padx=6,pady=(8,2))
        self.txt_context = scrolledtext.ScrolledText(frm_gen,height=12,wrap="word")
        self.txt_context.grid(row=1,column=0,columnspan=5,sticky="nsew",padx=6)
        try:
            with open("context_default.txt","r",encoding="utf-8") as f:
                self.txt_context.insert("1.0", f.read())
        except Exception:
            pass
        tk.Label(frm_gen,text="Daily Goals",font=("Segoe UI",11,"bold")).grid(row=2,column=0,sticky="w",padx=6,pady=(8,2))
        self.txt_goals = scrolledtext.ScrolledText(frm_gen,height=8,wrap="word")
        self.txt_goals.grid(row=3,column=0,columnspan=5,sticky="nsew",padx=6)

        frm_gen.rowconfigure(1, weight=1); frm_gen.rowconfigure(3, weight=1)
        for c in range(5): frm_gen.columnconfigure(c, weight=1)

        btns = ttk.Frame(frm_gen); btns.grid(row=4,column=0,columnspan=5,sticky="w",padx=6,pady=8)
        ttk.Button(btns,text="Upload Context (.txt)",command=self.load_context_file).grid(row=0,column=0,padx=4)
        ttk.Button(btns,text="Upload Goals (.txt)",command=self.load_goals_file).grid(row=0,column=1,padx=4)
        ttk.Button(btns,text="Save as Default Context",command=self.save_context_default).grid(row=0,column=2,padx=4)
        ttk.Button(btns,text="Generate JSON Schedule",command=self.on_generate).grid(row=0,column=3,padx=10)
        ttk.Button(btns,text="Open Output Folder",command=lambda: open_folder(".")).grid(row=0,column=4,padx=4)

        tk.Label(frm_gen,text="Preview (JSON)",font=("Segoe UI",11,"bold")).grid(row=5,column=0,sticky="w",padx=6)
        self.txt_preview = scrolledtext.ScrolledText(frm_gen,height=12,wrap="none")
        self.txt_preview.grid(row=6,column=0,columnspan=5,sticky="nsew",padx=6,pady=(0,8))
        frm_gen.rowconfigure(6, weight=1)

        # Run Alarms
        frm_run = ttk.Frame(nb); nb.add(frm_run, text="Run Alarms")
        ttk.Label(frm_run, text="Click Start to begin. Popups will ring until you interact.", font=("Segoe UI",11)).pack(pady=8)
        ttk.Button(frm_run, text="Start Alarms", command=self.on_start_alarms).pack(pady=6)

        # Smart AI Settings
        frm_ai = ttk.Frame(nb); nb.add(frm_ai, text="Smart AI Settings")
        self.var_save = tk.BooleanVar(value=self.settings.get("save_progress",True))
        self.var_reminders = tk.BooleanVar(value=self.settings.get("daily_ai_reminders",True))
        self.var_autoreroll = tk.BooleanVar(value=self.settings.get("auto_reroll_missed",True))
        self.var_cloud = tk.BooleanVar(value=self.settings.get("cloud_backup_enabled",False))
        self.var_interval = tk.StringVar(value=str(self.settings.get("reminder_interval_min",120)))
        ttk.Checkbutton(frm_ai,text="Save task progress automatically",variable=self.var_save).grid(row=0,column=0,sticky="w",padx=8,pady=6)
        ttk.Checkbutton(frm_ai,text="Daily AI reminders (looping notifications)",variable=self.var_reminders).grid(row=1,column=0,sticky="w",padx=8,pady=6)
        ttk.Label(frm_ai,text="Reminder interval (minutes):").grid(row=2,column=0,sticky="w",padx=8,pady=6)
        ttk.Entry(frm_ai,textvariable=self.var_interval,width=10).grid(row=2,column=1,sticky="w",padx=4,pady=6)
        ttk.Checkbutton(frm_ai,text="Enable cloud backup (manual export)",variable=self.var_cloud).grid(row=3,column=0,sticky="w",padx=8,pady=6)
        ttk.Button(frm_ai,text="Save Smart Settings",command=self.on_save_ai).grid(row=4,column=0,sticky="w",padx=8,pady=10)
        ttk.Button(frm_ai,text="Export schedule.json…",command=self.export_schedule).grid(row=4,column=1,sticky="w",padx=8,pady=10)

        # Settings
        frm_set = ttk.Frame(nb); nb.add(frm_set, text="Settings")
        ttk.Label(frm_set,text="OpenAI API Key:",font=("Segoe UI",11)).grid(row=0,column=0,sticky="w",padx=6,pady=(12,4))
        self.var_key = tk.StringVar(value=self.settings.get("api_key",""))
        ttk.Entry(frm_set,show="*",textvariable=self.var_key,width=56).grid(row=0,column=1,sticky="w",padx=6)
        ttk.Label(frm_set,text="Model:",font=("Segoe UI",11)).grid(row=1,column=0,sticky="w",padx=6,pady=4)
        self.var_model = tk.StringVar(value=self.settings.get("model","gpt-4o-mini"))
        ttk.Entry(frm_set,textvariable=self.var_model,width=24).grid(row=1,column=1,sticky="w",padx=6)
        ttk.Button(frm_set,text="Save Settings",command=self.on_save).grid(row=2,column=0,columnspan=2,padx=6,pady=10)

        # INSTRUCTIONS
        frm_help = ttk.Frame(nb); nb.add(frm_help, text="INSTRUCTIONS")
        txt_instr = scrolledtext.ScrolledText(frm_help, wrap="word")
        txt_instr.pack(fill="both", expand=True, padx=8, pady=8)
        _instructions_text = """AI Scheduler — Personal Power Mode

1) Settings → paste your OpenAI API key → Save.
2) Generate Schedule → enter/upload Context + Goals → Generate JSON → Preview.
3) Run Alarms → Start Alarms → interact with popups (NEXT / CHANGE TIME / STOP).
4) Smart AI Settings → toggle Save Progress, Reminders, Auto Reroll, etc.
5) Optional: Export schedule.json for manual cloud backup.
Time format: HH:MM-HH:MM (24-hr). Timezone in JSON defaults to KST.
"""
        txt_instr.insert("1.0", _instructions_text); txt_instr.configure(state="disabled")

    # Handlers
    def load_context_file(self):
        path = filedialog.askopenfilename(title="Select Context (.txt)", filetypes=[("Text files","*.txt")])
        if not path: return
        with open(path,"r",encoding="utf-8") as f:
            self.txt_context.delete("1.0","end"); self.txt_context.insert("1.0", f.read())

    def load_goals_file(self):
        path = filedialog.askopenfilename(title="Select Goals (.txt)", filetypes=[("Text files","*.txt")])
        if not path: return
        with open(path,"r",encoding="utf-8") as f:
            self.txt_goals.delete("1.0","end"); self.txt_goals.insert("1.0", f.read())

    def save_context_default(self):
        try:
            content = self.txt_context.get("1.0","end").strip()
            with open("context_default.txt","w",encoding="utf-8") as f: f.write(content)
            messagebox.showinfo("Saved","Default context saved.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_generate(self):
        goals = self.txt_goals.get("1.0","end").strip()
        context = self.txt_context.get("1.0","end").strip()
        if not goals or not context:
            messagebox.showerror("Missing","Please provide both Context and Goals.")
            return
        try:
            data = generate_schedule(goals, context)
            self.txt_preview.delete("1.0","end")
            self.txt_preview.insert("1.0", json.dumps(data, ensure_ascii=False, indent=2))
            messagebox.showinfo("Done","Saved schedule.json and dated copy in this folder.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_start_alarms(self):
        def runner():
            try:
                start_alarm_loop("schedule.json", poll_seconds=30)
            except Exception as e:
                messagebox.showerror("Alarm Error", str(e))
        threading.Thread(target=runner, daemon=True).start()
        messagebox.showinfo("Alarms","Alarm loop started. Popups will appear at block start times.")

    def on_save_ai(self):
        self.settings["save_progress"] = True if hasattr(self, "var_save") and self.var_save.get() else False
        self.settings["daily_ai_reminders"] = True if hasattr(self, "var_reminders") and self.var_reminders.get() else False
        try:
            self.settings["reminder_interval_min"] = int(self.var_interval.get().strip())
        except Exception:
            self.settings["reminder_interval_min"] = 120
        self.settings["auto_reroll_missed"] = True if hasattr(self, "var_autoreroll") and self.var_autoreroll.get() else False
        self.settings["cloud_backup_enabled"] = True if hasattr(self, "var_cloud") and self.var_cloud.get() else False
        save_settings(self.settings)
        messagebox.showinfo("Saved","Smart settings saved.")

    def export_schedule(self):
        if not os.path.exists("schedule.json"):
            messagebox.showerror("No schedule","Please generate a schedule first.")
            return
        dest = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")], title="Export schedule.json")
        if not dest: return
        with open("schedule.json","r",encoding="utf-8") as f:
            data = f.read()
        with open(dest,"w",encoding="utf-8") as out:
            out.write(data)
        messagebox.showinfo("Exported","schedule.json exported.")

    def on_save(self):
        self.settings["api_key"] = self.var_key.get().strip()
        self.settings["model"] = self.var_model.get().strip() or "gpt-4o-mini"
        save_settings(self.settings)
        messagebox.showinfo("Saved","Settings saved.")

if __name__=="__main__":
    app = App()
    app.mainloop()
