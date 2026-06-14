# -*- coding: utf-8 -*-
"""
Stage 1 GUI Wrapper (Tkinter)
- File pickers for Master/Warehouse
- Optional output path
- Progress log window
- Single "Run" button
"""
import threading, queue
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from stage1_standalone import run_sync

APP_TITLE = "HVDC Stage 1 – Synchronizer"
DEFAULT_OUT_NAME = "Stage1_Sync_Output.xlsx"

class LogConsole(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.text = tk.Text(self, height=18, wrap="word")
        self.text.configure(state="disabled")
        yscroll = ttk.Scrollbar(self, command=self.text.yview)
        self.text.configure(yscrollcommand=yscroll.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def append(self, msg: str):
        self.text.configure(state="normal")
        self.text.insert("end", msg)
        self.text.see("end")
        self.text.configure(state="disabled")
        self.update_idletasks()

class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.master = master
        self.master.title(APP_TITLE)

        # Inputs
        self.master_path = tk.StringVar()
        self.wh_path = tk.StringVar()
        self.out_path = tk.StringVar()

        # Row 0: Master
        ttk.Label(self, text="Master (.xlsx)").grid(row=0, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.master_path, width=50).grid(row=0, column=1, sticky="ew")
        ttk.Button(self, text="Browse...", command=self.pick_master).grid(row=0, column=2, padx=6)

        # Row 1: Warehouse
        ttk.Label(self, text="Warehouse (.xlsx)").grid(row=1, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.wh_path, width=50).grid(row=1, column=1, sticky="ew")
        ttk.Button(self, text="Browse...", command=self.pick_wh).grid(row=1, column=2, padx=6)

        # Row 2: Output (optional)
        ttk.Label(self, text="Output (.xlsx)").grid(row=2, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.out_path, width=50).grid(row=2, column=1, sticky="ew")
        ttk.Button(self, text="Save As...", command=self.pick_out).grid(row=2, column=2, padx=6)

        # Row 3: Run
        self.run_btn = ttk.Button(self, text="Run Stage 1", command=self.on_run)
        self.run_btn.grid(row=3, column=0, columnspan=3, pady=(6, 6), sticky="ew")

        # Row 4: Console
        self.console = LogConsole(self)
        self.console.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(6, 0))

        # Layout
        self.grid(row=0, column=0, sticky="nsew")
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def pick_master(self):
        p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx;*.xlsm;*.xls")])
        if p: self.master_path.set(p)

    def pick_wh(self):
        p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx;*.xlsm;*.xls")])
        if p: self.wh_path.set(p)

    def pick_out(self):
        p = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=DEFAULT_OUT_NAME)
        if p: self.out_path.set(p)

    def on_run(self):
        master = self.master_path.get().strip()
        wh = self.wh_path.get().strip()
        out = self.out_path.get().strip() or None
        if not master or not wh:
            messagebox.showwarning("Missing Inputs", "Please select Master and Warehouse files.")
            return

        self.run_btn.configure(state="disabled")
        self.console.append(">> Running Stage 1 synchronization...\n")

        def log_cb(s: str):
            self.console.append(s)

        def worker():
            try:
                ok, out_path, stats = run_sync(master, wh, out, log_cb=log_cb)
                if ok:
                    self.console.append(f"\n[OK] Output written to: {out_path}\n")
                    messagebox.showinfo("Completed", f"Output written to:\n{out_path}")
                else:
                    messagebox.showerror("Failed", "Synchronization failed. See log for details.")
            except Exception as e:
                self.console.append(f"\n[ERROR] {e}\n")
                messagebox.showerror("Error", str(e))
            finally:
                self.run_btn.configure(state="normal")

        threading.Thread(target=worker, daemon=True).start()

def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    App(root)
    root.minsize(720, 480)
    root.mainloop()

if __name__ == "__main__":
    main()

