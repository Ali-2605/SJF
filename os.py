import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SJFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SJF Preemptive Scheduling Simulator")
        self.applyDarkMode()
        
        self.processes = []
        self.ganttData = []
        
        self.createWidgets()

    def applyDarkMode(self):
        style = ttk.Style(self.root)
        self.root.configure(bg="#2e2e2e")
        style.theme_use("default")

        style.configure(".", background="#2e2e2e", foreground="white", fieldbackground="#3e3e3e")
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TLabel", background="#2e2e2e", foreground="white")
        style.configure("TEntry", fieldbackground="#3e3e3e", foreground="white")
        style.configure("TButton", background="#3e3e3e", foreground="white")
        style.configure("Treeview", background="#3e3e3e", fieldbackground="#3e3e3e", foreground="white")
        style.configure("Treeview.Heading", background="#1e1e1e", foreground="white")

    def createWidgets(self):
        mainFrame = ttk.Frame(self.root, padding=10)
        mainFrame.pack(fill=tk.BOTH, expand=True)
        
        # simple Frame instead of LabelFrame
        inputFrame = ttk.Frame(mainFrame, padding=10)
        inputFrame.pack(fill=tk.X, pady=5)
        
        ttk.Label(inputFrame, text="Number of Processes (1–10):").grid(row=0, column=0, padx=5)
        self.numProcesses = tk.Entry(inputFrame, width=10, validate="key")
        vcmd = (self.numProcesses.register(self.validateNumber), '%P')
        self.numProcesses.config(validatecommand=vcmd)
        self.numProcesses.grid(row=0, column=1, padx=5)
        
        ttk.Button(inputFrame, text="Create Process Table", command=self.createProcessTable).grid(row=0, column=2, padx=5)
        
        self.tableFrame = ttk.Frame(mainFrame)
        self.tableFrame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.resultsFrame = ttk.Frame(mainFrame)
        
        ttk.Button(mainFrame, text="Run Simulation", command=self.runSimulation).pack(pady=5)

    def validateNumber(self, value):
        return value.isdigit() or value == ""

    def createProcessTable(self):
        # Clear any previous table
        for widget in self.tableFrame.winfo_children():
            widget.destroy()
        
        # Validate and limit number of processes
        try:
            n = int(self.numProcesses.get())
            if not (1 <= n <= 10):
                raise ValueError
        except:
            messagebox.showerror("Error", "Please enter a valid number of processes (1–10).")
            return
        
        # Header row
        ttk.Label(self.tableFrame, text="Process").grid(row=0, column=0, padx=5)
        ttk.Label(self.tableFrame, text="Arrival Time").grid(row=0, column=1, padx=5)
        ttk.Label(self.tableFrame, text="Burst Time").grid(row=0, column=2, padx=5)
        
        # Entry rows
        self.processEntries = []
        for i in range(n):
            ttk.Label(self.tableFrame, text=f"P{i+1}").grid(row=i+1, column=0, padx=5)
            arrival = tk.Entry(self.tableFrame, width=10, validate="key")
            arrival.config(validatecommand=(arrival.register(self.validateNumber), '%P'))
            arrival.grid(row=i+1, column=1, padx=5)
            burst = tk.Entry(self.tableFrame, width=10, validate="key")
            burst.config(validatecommand=(burst.register(self.validateNumber), '%P'))
            burst.grid(row=i+1, column=2, padx=5)
            self.processEntries.append((arrival, burst))

    def runSimulation(self):
        # 1) Check that the table has been created
        if not hasattr(self, 'processEntries') or len(self.processEntries) == 0:
            messagebox.showerror("Error", "Please create the process table first.")
            return

        # 2) Read & validate process inputs
        try:
            self.processes = []
            for i, (arrivalEntry, burstEntry) in enumerate(self.processEntries):
                arrival_str = arrivalEntry.get().strip()
                burst_str   = burstEntry.get().strip()
                # Check for empty fields
                if arrival_str == "" or burst_str == "":
                    messagebox.showerror("Error", "Please fill in all arrival and burst times.")
                    return
                arrival = int(arrival_str)
                burst   = int(burst_str)
                if arrival < 0 or burst <= 0:
                    raise ValueError
                self.processes.append({
                    'pid': i+1,
                    'arrival': arrival,
                    'burst': burst,
                    'remaining': burst,
                    'start_time': -1,
                    'finish_time': -1,
                    'waiting': 0,
                    'response': -1
                })
        except ValueError:
            messagebox.showerror("Error", "Invalid input values! Arrival must be ≥ 0 and Burst > 0.")
            return
        
        # All good → run, calculate, and display
        self.simulateSJF()
        self.calculateMetrics()
        self.showResults()

    def simulateSJF(self):
        time = 0
        completed = 0
        currentPid = -1
        n = len(self.processes)
        self.ganttData = []
        
        while completed < n:
            ready = [p for p in self.processes if p['arrival'] <= time and p['remaining'] > 0]
            if not ready:
                time += 1
                continue
            
            shortest = min(ready, key=lambda p: p['remaining'])
            
            if shortest['pid'] != currentPid:
                if currentPid != -1 and self.processes[currentPid-1]['remaining'] > 0:
                    self.ganttData[-1]['end'] = time
                currentPid = shortest['pid']
                if shortest['response'] == -1:
                    shortest['response'] = time - shortest['arrival']
                if shortest['start_time'] == -1:
                    shortest['start_time'] = time
                self.ganttData.append({'pid': currentPid, 'start': time, 'end': time+1})
            else:
                self.ganttData[-1]['end'] += 1
            
            shortest['remaining'] -= 1
            time += 1
            
            if shortest['remaining'] == 0:
                completed += 1
                shortest['finish_time'] = time
                currentPid = -1

    def calculateMetrics(self):
        totalW = totalT = totalR = 0
        for p in self.processes:
            p['turnaround'] = p['finish_time'] - p['arrival']
            p['waiting']    = p['turnaround'] - p['burst']
            totalW += p['waiting']
            totalT += p['turnaround']
            totalR += p['response']
        self.avgWaiting    = totalW / len(self.processes)
        self.avgTurnaround = totalT / len(self.processes)
        self.avgResponse   = totalR / len(self.processes)

    def showResults(self):
        for widget in self.resultsFrame.winfo_children():
            widget.destroy()
        self.resultsFrame.pack(fill=tk.BOTH, expand=True, pady=10)

        leftFrame = ttk.Frame(self.resultsFrame)
        leftFrame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        rightFrame = ttk.Frame(self.resultsFrame)
        rightFrame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        cols = ('PID','Arrival','Burst','Finish','Waiting','Turnaround','Response')
        tree = ttk.Treeview(leftFrame, columns=cols, show='headings', height=10)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=80, anchor=tk.CENTER)
        for p in self.processes:
            tree.insert('', tk.END, values=(
                p['pid'], p['arrival'], p['burst'],
                p['finish_time'], p['waiting'],
                p['turnaround'], p['response']
            ))
        tree.pack(pady=5)

        avgF = ttk.Frame(leftFrame, padding=5)
        avgF.pack(pady=5)
        ttk.Label(avgF, text=f"Average Waiting Time: {self.avgWaiting:.2f}").pack(pady=2)
        ttk.Label(avgF, text=f"Average Turnaround Time: {self.avgTurnaround:.2f}").pack(pady=2)
        ttk.Label(avgF, text=f"Average Response Time: {self.avgResponse:.2f}").pack(pady=2)

        self.createGanttChart(rightFrame)

    def createGanttChart(self, parent):
        fig = Figure(figsize=(6,4), dpi=100)
        ax = fig.add_subplot(111)
        yTicks = []; yLabels = []
        for i, ev in enumerate(self.ganttData):
            ax.broken_barh([(ev['start'], ev['end']-ev['start'])], (i,1), facecolors=('tab:blue'))
            yTicks.append(i+0.5); yLabels.append(f"P{ev['pid']}")
        ax.set_yticks(yTicks); ax.set_yticklabels(yLabels)
        ax.set_xlabel("Time"); ax.set_title("Gantt Chart")
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = SJFApp(root)
    root.mainloop()
