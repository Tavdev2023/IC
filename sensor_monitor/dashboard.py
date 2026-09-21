import argparse
import random
import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .analyzer import analyze_measurements
from .csv_input import read_measurements
from .models import Measurement
from .plotting import draw_dashboard
from .report import format_temperature, summary_text
from .simulator import generate_transformer_measurements


class TransformerDashboard:
    def __init__(
        self, root: tk.Tk, input_path: Optional[str] = None, seed: Optional[int] = None
    ) -> None:
        self.root = root
        self.root.title("Monitor térmico do transformador")
        self.root.geometry("1100x760")
        self.measurements: list[Measurement] = []

        controls = ttk.Frame(root, padding=(12, 12, 12, 0))
        controls.pack(fill="x")
        ttk.Label(controls, text="Limite de mudança (°C):").pack(side="left")
        self.threshold = tk.StringVar(value="5")
        ttk.Entry(controls, textvariable=self.threshold, width=8).pack(side="left", padx=8)
        ttk.Button(controls, text="Atualizar análise", command=self.refresh).pack(side="left")
        ttk.Label(controls, text="Semente:").pack(side="left", padx=(20, 0))
        self.seed = tk.StringVar(value="" if seed is None else str(seed))
        ttk.Entry(controls, textvariable=self.seed, width=10).pack(side="left", padx=8)
        ttk.Button(controls, text="Usar simulação", command=self.use_simulation).pack(side="left")
        ttk.Button(controls, text="Abrir CSV...", command=self.open_csv).pack(side="left", padx=(20, 0))
        self.source = tk.StringVar()
        ttk.Label(controls, textvariable=self.source).pack(side="left", padx=12)

        self.summary = ttk.Label(root, text="", padding=(12, 8))
        self.summary.pack(fill="x")

        self.figure = Figure(figsize=(10, 4.5), dpi=100)
        self.axes = self.figure.subplots(1, 2)
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=12)

        table = ttk.Frame(root, padding=(12, 0, 12, 12))
        table.pack(fill="x")
        self.readings = ttk.Treeview(
            table, columns=("time", "value", "note"), show="headings", height=10
        )
        for column, title, width in (
            ("time", "Horário", 90),
            ("value", "Valor", 110),
            ("note", "Observação", 320),
        ):
            self.readings.heading(column, text=title)
            self.readings.column(column, width=width, anchor="w")
        scrollbar = ttk.Scrollbar(table, orient="vertical", command=self.readings.yview)
        self.readings.configure(yscrollcommand=scrollbar.set)
        self.readings.pack(side="left", fill="x", expand=True)
        scrollbar.pack(side="right", fill="y")

        if input_path:
            self._load(lambda: read_measurements(input_path), input_path)
        else:
            self.use_simulation()

    def use_simulation(self) -> None:
        """Load a simulated run, drawing a seed when the field is left empty."""
        text = self.seed.get().strip()
        try:
            seed = int(text) if text else random.randrange(1_000_000)
        except ValueError:
            messagebox.showerror("Semente inválida", f"'{text}' não é um número inteiro.")
            return

        self.seed.set(str(seed))
        self._load(
            lambda: list(generate_transformer_measurements(seed)), f"simulação (semente {seed})"
        )

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

        notes = {
            id(change.current): f"mudança brusca ({change.difference:.2f} °C)"
            for change in result.sudden_changes
        }
        for item in self.readings.get_children():
            self.readings.delete(item)
        for measurement in self.measurements:
            value = format_temperature(measurement.value if measurement.is_valid else None)
            self.readings.insert(
                "", "end", values=(measurement.timestamp, value, notes.get(id(measurement), ""))
            )


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Interface gráfica de análise de medições.")
    parser.add_argument("--input", metavar="ARQUIVO", help="CSV com colunas 'horário,valor' para abrir ao iniciar")
    parser.add_argument("--seed", type=int, metavar="N", help="semente do simulador ao iniciar")
    args = parser.parse_args(argv)

    root = tk.Tk()
    TransformerDashboard(root, args.input, args.seed)
    root.mainloop()


if __name__ == "__main__":
    main()
