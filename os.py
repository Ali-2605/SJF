import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle

class SJFApp:
    def __init__(self, root):
        """Initialize the application with dark theme and main window setup"""
        self.root = root
        self.root.title("SJF Preemptive Scheduling Simulator")
        self.applyDarkMode()  # Set up dark theme
        
        # Store process information and Gantt chart data
        self.processes = []
        self.ganttData = []
        
        self.createInputWidgets()  # Build the user interface

    def applyDarkMode(self):
        """Configure dark theme colors and styles for all widgets"""
        style = ttk.Style(self.root)
        self.root.configure(bg="#2e2e2e")  # Main background color
        
        # Configure colors for different widget types
        style.configure(".", background="#2e2e2e", foreground="white", fieldbackground="#3e3e3e")
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TLabel", background="#2e2e2e", foreground="white")
        style.configure("TEntry", fieldbackground="#3e3e3e", foreground="white")
        style.configure("TButton", background="#3e3e3e", foreground="white")
        style.configure("Treeview", background="#3e3e3e", fieldbackground="#3e3e3e", foreground="white")
        style.configure("Treeview.Heading", background="#1e1e1e", foreground="white")

    def createInputWidgets(self):
        """Create the main user interface with input controls"""
        mainFrame = ttk.Frame(self.root, padding=10)
        mainFrame.pack(fill=tk.BOTH, expand=True)
        
        # Input controls frame
        inputFrame = ttk.Frame(mainFrame, padding=10)
        inputFrame.pack(fill=tk.X, pady=5)
        
        # Number of processes input
        ttk.Label(inputFrame, text="Number of Processes (1-10):").grid(row=0, column=0, padx=5)
        self.numProcessesInput = tk.Entry(inputFrame, width=10, validate="key")
        validationCommand = (self.numProcessesInput.register(self.validateNumberInput), '%P')
        self.numProcessesInput.config(validatecommand=validationCommand)
        self.numProcessesInput.grid(row=0, column=1, padx=5)
        
        # Button to create process table
        ttk.Button(inputFrame, text="Create Process Table", command=self.createProcessInputTable).grid(row=0, column=2, padx=5)
        
        # Container for process input table
        self.processTableFrame = ttk.Frame(mainFrame)
        self.processTableFrame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Results display area
        self.resultsFrame = ttk.Frame(mainFrame)
        
        # Simulation start button
        ttk.Button(mainFrame, text="Run Simulation", command=self.runSimulation).pack(pady=5)

    def validateNumberInput(self, value):
        """Validate that input contains only digits (for number fields)"""
        return value.isdigit() or value == ""

    def createProcessInputTable(self):
        """Create a table where users can input process arrival and burst times"""
        # Clear previous table if exists
        for widget in self.processTableFrame.winfo_children():
            widget.destroy()
        
        try:
            numProcesses = int(self.numProcessesInput.get())
            if not (1 <= numProcesses <= 10):
                raise ValueError
        except:
            messagebox.showerror("Error", "Please enter a valid number of processes (1-10).")
            return
        
        # Create table headers
        ttk.Label(self.processTableFrame, text="Process").grid(row=0, column=0, padx=5)
        ttk.Label(self.processTableFrame, text="Arrival Time").grid(row=0, column=1, padx=5)
        ttk.Label(self.processTableFrame, text="Burst Time").grid(row=0, column=2, padx=5)
        
        # Create input rows for each process
        self.processInputs = []
        for i in range(numProcesses):
            ttk.Label(self.processTableFrame, text=f"P{i+1}").grid(row=i+1, column=0, padx=5)
            arrivalInput = tk.Entry(self.processTableFrame, width=10, validate="key")
            arrivalInput.config(validatecommand=(arrivalInput.register(self.validateNumberInput), '%P'))
            arrivalInput.grid(row=i+1, column=1, padx=5)
            burstInput = tk.Entry(self.processTableFrame, width=10, validate="key")
            burstInput.config(validatecommand=(burstInput.register(self.validateNumberInput), '%P'))
            burstInput.grid(row=i+1, column=2, padx=5)
            self.processInputs.append((arrivalInput, burstInput))

    def runSimulation(self):
        """Main function to run the scheduling simulation and display results"""
        # Check if process table exists
        if not hasattr(self, 'processInputs') or len(self.processInputs) == 0:
            messagebox.showerror("Error", "Please create the process table first.")
            return

        # Read and validate process inputs
        try:
            self.processes = []
            for i, (arrivalEntry, burstEntry) in enumerate(self.processInputs):
                arrivalTime = arrivalEntry.get().strip()
                burstTime = burstEntry.get().strip()
                
                if arrivalTime == "" or burstTime == "":
                    messagebox.showerror("Error", "Please fill in all arrival and burst times.")
                    return
                
                # Convert inputs to integers and validate
                arrivalTime = int(arrivalTime)
                burstTime = int(burstTime)
                if arrivalTime < 0 or burstTime <= 0:
                    raise ValueError
                
                # Store process information
                self.processes.append({'pid': i+1, 'arrival': arrivalTime, 'burst': burstTime, 'remaining': burstTime, 'start_time': -1,'finish_time': -1, 'waiting': 0, 'response': -1
                })

        except ValueError:
            messagebox.showerror("Error", "Invalid input values! Arrival must be ≥ 0 and Burst > 0.")
            return
        
        self.executeSJFAlgorithm()
        self.calculatePerformanceMetrics()
        self.displayResults()

    def executeSJFAlgorithm(self):
        """Implement the Shortest Job First (Preemptive) scheduling algorithm"""
        currentTime = 0
        completedProcesses = 0
        currentProcessId = -1
        totalProcesses = len(self.processes)
        self.ganttData = []  # Store timeline for Gantt chart
        
        while completedProcesses < totalProcesses:
            # Find processes that have arrived and still need CPU time
            readyProcesses = [p for p in self.processes 
                             if p['arrival'] <= currentTime and p['remaining'] > 0]
            
            if not readyProcesses:
                currentTime += 1
                continue
            
            # Select process with shortest remaining time
            shortestJob = min(readyProcesses, key=lambda p: p['remaining'])
            
            if shortestJob['pid'] != currentProcessId:
                # Record previous process execution end time
                if currentProcessId != -1 and self.processes[currentProcessId - 1]['remaining'] > 0:
                    self.ganttData[-1]['end'] = currentTime
                currentProcessId = shortestJob['pid']
                
                # Record response time (first time process gets CPU)
                if shortestJob['response'] == -1:
                    shortestJob['response'] = currentTime - shortestJob['arrival']
                
                # Record process start time and create new Gantt entry
                if shortestJob['start_time'] == -1:
                    shortestJob['start_time'] = currentTime
                self.ganttData.append({'pid': currentProcessId, 'start': currentTime, 'end': currentTime+1})
            else:
                # Extend current process execution time
                self.ganttData[-1]['end'] += 1
            
            # Update process remaining time and global clock
            shortestJob['remaining'] -= 1
            currentTime += 1
            
            # Check if process completed
            if shortestJob['remaining'] == 0:
                completedProcesses += 1
                shortestJob['finish_time'] = currentTime
                currentProcessId = -1

    def calculatePerformanceMetrics(self):
        """Calculate waiting, turnaround, and response times for all processes"""
        totalWaiting = totalTurnaround = totalResponse = 0
        for process in self.processes:
            process['turnaround'] = process['finish_time'] - process['arrival']
            process['waiting'] = process['turnaround'] - process['burst']
            totalWaiting += process['waiting']
            totalTurnaround += process['turnaround']
            totalResponse += process['response']
        
        # Calculate averages
        self.avgWaiting = totalWaiting / len(self.processes)
        self.avgTurnaround = totalTurnaround / len(self.processes)
        self.avgResponse = totalResponse / len(self.processes)

    def displayResults(self):
        """Show simulation results including table and Gantt chart"""
        # Clear previous results
        for widget in self.resultsFrame.winfo_children():
            widget.destroy()
        self.resultsFrame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create results table frame
        tableFrame = ttk.Frame(self.resultsFrame)
        tableFrame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Create Gantt chart frame
        chartFrame = ttk.Frame(self.resultsFrame)
        chartFrame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create results table
        columns = ('PID','Arrival','Burst','Finish','Waiting','Turnaround','Response')
        resultsTable = ttk.Treeview(tableFrame, columns=columns, show='headings', height=10)
        for col in columns:
            resultsTable.heading(col, text=col)
            resultsTable.column(col, width=80, anchor=tk.CENTER)
        
        # Populate table with process data
        for process in self.processes:
            resultsTable.insert('', tk.END, values=(
                process['pid'], process['arrival'], process['burst'],
                process['finish_time'], process['waiting'],
                process['turnaround'], process['response']
            ))
        resultsTable.pack(pady=5)

        # Display average metrics
        metricsFrame = ttk.Frame(tableFrame, padding=5)
        metricsFrame.pack(pady=5)
        ttk.Label(metricsFrame, text=f"Average Waiting Time: {self.avgWaiting:.2f}").pack(pady=2)
        ttk.Label(metricsFrame, text=f"Average Turnaround Time: {self.avgTurnaround:.2f}").pack(pady=2)
        ttk.Label(metricsFrame, text=f"Average Response Time: {self.avgResponse:.2f}").pack(pady=2)

        # Draw Gantt chart
        self.createGanttChart(chartFrame)

    def createGanttChart(self, parent):
        """Create a Gantt chart visualization using matplotlib"""
        fig = Figure(figsize=(6, 2), dpi=100)
        chartAxis = fig.add_subplot(111)
        
        # Create colored bars for each process execution
        for timeSegment in self.ganttData:
            startTime = timeSegment['start']
            endTime = timeSegment['end']
            duration = endTime - startTime
            processId = timeSegment['pid']
            
            # Create rectangle representing process execution time
            bar = Rectangle((startTime, 0), duration, 1,
                           facecolor='tab:blue', edgecolor='black')
            chartAxis.add_patch(bar)
            
            # Add process ID label
            chartAxis.text(startTime + duration/2, 0.5, f"P{processId}",
                          ha='center', va='center', color='white', fontsize=10)
        
        # Configure chart appearance
        timeTicks = sorted({t for segment in self.ganttData for t in (segment['start'], segment['end'])})
        chartAxis.set_xticks(timeTicks)
        chartAxis.set_xticklabels([str(t) for t in timeTicks])
        chartAxis.set_ylim(0, 1)
        chartAxis.set_yticks([])
        chartAxis.set_xlabel("Time")
        chartAxis.set_title("Execution Timeline")
        chartAxis.grid(axis='x', linestyle='--', alpha=0.4)

        # Embed chart in Tkinter window
        chartCanvas = FigureCanvasTkAgg(fig, master=parent)
        chartCanvas.draw()
        chartCanvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = SJFApp(root)
    root.mainloop()