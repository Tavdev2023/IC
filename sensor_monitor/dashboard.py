import argparse
import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from sensor_monitor.analyzer import analyze_measurements
from sensor_monitor.csv_input import read_measurements
from sensor_monitor.models import Measurement
from sensor_monitor.plotting import draw_dashboard
from sensor_monitor.report import summary_text
from sensor_monitor.simulator import generate_transformer_measurements


class TransformerDashboard:
    def __init__(self, root: tk.Tk, input_path: Optional[str] = None) -> None:
        self.root = root
        self.root.title("Monitor térmico do transformador")
        self.root.geometry("1100x760")
        self.measurements: list[Measurement] = []

        controls = ttk.Frame(root, padding=(12, 12, 12, 0))
        controls.pack(fill="x")
        ttk.Label(controls, text="Limite de mudança (°C):").pack(side="left")
        self.threshold = tk.StringVar(value="10")
        ttk.Entry(controls, textvariable=self.threshold, width=8).pack(side="left", padx=8)
        ttk.Button(controls, text="Atualizar análise", command=self.refresh).pack(side="left")
        ttk.Button(controls, text="Abrir CSV...", command=self.open_csv).pack(side="left", padx=(20, 0))
        ttk.Button(controls, text="Usar simulação", command=self.use_simulation).pack(side="left", padx=8)
        self.source = tk.StringVar()
        ttk.Label(controls, textvariable=self.source).pack(side="left", padx=12)

        self.summary = ttk.Label(root, text="", padding=(12, 8))
        self.summary.pack(fill="x")

        self.figure = Figure(figsize=(10, 5.5), dpi=100)
        self.axes = self.figure.subplots(1, 2)
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=12)
        self.events = ttk.Treeview(root, columns=("from", "to", "difference"), show="headings", height=5)
        for column, title in (("from", "De"), ("to", "Para"), ("difference", "Diferença (°C)")):
            self.events.heading(column, text=title)
        self.events.pack(fill="x", padx=12, pady=(0, 12))

        if input_path:
            self._load(lambda: read_measurements(input_path), input_path)
        else:
            self.use_simulation()

    def use_simulation(self) -> None:
        self._load(lambda: list(generate_transformer_measurements()), "simulação")

    def open_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="Abrir medições", filetypes=[("CSV", "*.csv"), ("Todos os arquivos", "*.*")]
        )
        if path:
            self._load(lambda: read_measurements(path), path)

    def _load(self, loader: Callable[[], list[Measurement]], source: str) -> None:
        try:
            measurements = loader()
        except (OSError, ValueError) as error:
            messagebox.showerror("Não foi possível ler as medições", str(error))
            return
        self.measurements = measurements
        self.source.set(f"Fonte: {source}")
        self.refresh()

    def refresh(self) -> None:
        try:
            threshold = float(self.threshold.get())
            result = analyze_measurements(self.measurements, threshold)
        except ValueError as error:
            messagebox.showerror("Entrada inválida", str(error))
            return

        draw_dashboard(self.axes, self.measurements, result)
        self.figure.tight_layout()
        self.canvas.draw()
        self.summary.configure(text=summary_text(result))
        for item in self.events.get_children():
            self.events.delete(item)
        for change in result.sudden_changes:
            self.events.insert(
                "", "end", values=(change.previous.timestamp, change.current.timestamp, f"{change.difference:.1f}")
            )


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Interface gráfica de análise de medições.")
    parser.add_argument("--input", metavar="ARQUIVO", help="CSV com colunas 'horário,valor' para abrir ao iniciar")
    args = parser.parse_args(argv)

    root = tk.Tk()
    TransformerDashboard(root, args.input)
    root.mainloop()


if __name__ == "__main__":
    main()
