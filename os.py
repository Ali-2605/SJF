import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SJFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SJF Preemptive Scheduling Simulator")
        
        self.processes = []
        self.gantt_data = []
        
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input controls
        input_frame = ttk.LabelFrame(main_frame, text="Input Parameters", padding=10)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Number of Processes:").grid(row=0, column=0, padx=5)
        self.num_processes = tk.Entry(input_frame, width=10, validate="key")
        self.num_processes['validatecommand'] = (self.num_processes.register(self.validate_number), '%P')
        self.num_processes.grid(row=0, column=1, padx=5)
        
        ttk.Button(input_frame, text="Create Process Table", 
                  command=self.create_process_table).grid(row=0, column=2, padx=5)
        
        # Process table frame
        self.table_frame = ttk.Frame(main_frame)
        self.table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Results frame
        self.results_frame = ttk.Frame(main_frame)
        
        # Simulation button
        ttk.Button(main_frame, text="Run Simulation", 
                  command=self.run_simulation).pack(pady=5)
        
    def validate_number(self, value):
        return value.isdigit() or value == ""
    
    def create_process_table(self):
        # Clear previous table
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        try:
            n = int(self.num_processes.get())
            if n <= 0:
                raise ValueError
        except:
            messagebox.showerror("Error", "Please enter a valid number of processes")
            return
        
        # Create table headers
        ttk.Label(self.table_frame, text="Process").grid(row=0, column=0, padx=5)
        ttk.Label(self.table_frame, text="Arrival Time").grid(row=0, column=1, padx=5)
        ttk.Label(self.table_frame, text="Burst Time").grid(row=0, column=2, padx=5)
        
        # Create entry fields
        self.process_entries = []
        for i in range(n):
            ttk.Label(self.table_frame, text=f"P{i+1}").grid(row=i+1, column=0, padx=5)
            arrival = tk.Entry(self.table_frame, width=10, validate="key")
            arrival['validatecommand'] = (arrival.register(self.validate_number), '%P')
            arrival.grid(row=i+1, column=1, padx=5)
            burst = tk.Entry(self.table_frame, width=10, validate="key")
            burst['validatecommand'] = (burst.register(self.validate_number), '%P')
            burst.grid(row=i+1, column=2, padx=5)
            self.process_entries.append((arrival, burst))
        
    def run_simulation(self):
        try:
            # Get process data
            self.processes = []
            for i, (arrival_entry, burst_entry) in enumerate(self.process_entries):
                arrival = int(arrival_entry.get())
                burst = int(burst_entry.get())
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
        except:
            messagebox.showerror("Error", "Invalid input values! Ensure all fields are valid (arrival ≥ 0, burst > 0)")
            return
        
        # Run SJF Preemptive simulation
        self.simulate_sjf()
        
        # Calculate metrics
        self.calculate_metrics()
        
        # Display results
        self.show_results()
        
    def simulate_sjf(self):
        time = 0
        completed = 0
        current_pid = -1
        n = len(self.processes)
        self.gantt_data = []
        
        while completed < n:
            # Find arrived processes with remaining time
            ready = [p for p in self.processes if p['arrival'] <= time and p['remaining'] > 0]
            
            if not ready:
                time += 1
                continue
                
            # Find process with shortest remaining time
            shortest = min(ready, key=lambda x: x['remaining'])
            
            if shortest['pid'] != current_pid:
                if current_pid != -1 and self.processes[current_pid-1]['remaining'] > 0:
                    # Record preemption
                    self.gantt_data[-1]['end'] = time
                
                current_pid = shortest['pid']
                if shortest['response'] == -1:
                    shortest['response'] = time - shortest['arrival']
                if shortest['start_time'] == -1:
                    shortest['start_time'] = time
                self.gantt_data.append({
                    'pid': current_pid,
                    'start': time,
                    'end': time+1
                })
            else:
                self.gantt_data[-1]['end'] += 1
                
            shortest['remaining'] -= 1
            time += 1
            
            if shortest['remaining'] == 0:
                completed += 1
                shortest['finish_time'] = time
                current_pid = -1
                
    def calculate_metrics(self):
        total_waiting = 0
        total_turnaround = 0
        total_response = 0
        
        for p in self.processes:
            p['turnaround'] = p['finish_time'] - p['arrival']
            p['waiting'] = p['turnaround'] - p['burst']
            total_waiting += p['waiting']
            total_turnaround += p['turnaround']
            total_response += p['response']
            
        self.avg_waiting = total_waiting / len(self.processes)
        self.avg_turnaround = total_turnaround / len(self.processes)
        self.avg_response = total_response / len(self.processes)
        
    def show_results(self):
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Results table
        columns = ('PID', 'Arrival', 'Burst', 'Finish', 'Waiting', 'Turnaround', 'Response')
        tree = ttk.Treeview(self.results_frame, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=80, anchor=tk.CENTER)
            
        for p in self.processes:
            tree.insert('', tk.END, values=(
                p['pid'],
                p['arrival'],
                p['burst'],
                p['finish_time'],
                p['waiting'],
                p['turnaround'],
                p['response']
            ))
            
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Averages
        avg_frame = ttk.Frame(self.results_frame, padding=10)
        avg_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(avg_frame, text=f"Average Waiting Time: {self.avg_waiting:.2f}").pack(pady=5)
        ttk.Label(avg_frame, text=f"Average Turnaround Time: {self.avg_turnaround:.2f}").pack(pady=5)
        ttk.Label(avg_frame, text=f"Average Response Time: {self.avg_response:.2f}").pack(pady=5)
        
        # Gantt chart
        self.create_gantt_chart()
        
    def create_gantt_chart(self):
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        y_ticks = []
        y_labels = []
        
        for i, event in enumerate(self.gantt_data):
            ax.broken_barh([(event['start'], event['end'] - event['start'])],
                          (i, 1), facecolors=('tab:blue'))
            y_ticks.append(i + 0.5)
            y_labels.append(f"P{event['pid']}")
            
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
        ax.set_xlabel("Time")
        ax.set_title("Gantt Chart")
        
        canvas = FigureCanvasTkAgg(fig, master=self.results_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = SJFApp(root)
    root.mainloop()