import threading
import tkinter as tk

from datetime import datetime
from tkinter import messagebox, ttk

from openij.client import CanonClient


class OpenIJApp:
    """Interface graphique principale d'OpenIJ."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("OpenIJ")
        self.root.geometry("760x620")
        self.root.minsize(680, 560)

        self.client: CanonClient | None = None
        self.is_busy = False

        self.ip_var = tk.StringVar(value="192.168.1.173")
        self.status_var = tk.StringVar(value="Non connectée")
        self.activity_var = tk.StringVar(value="Prêt")

        self._configure_style()
        self._build_interface()

        self.log("OpenIJ démarré.")
        self.log("Saisissez l'adresse IP de l'imprimante puis cliquez sur Tester.")

    def _configure_style(self) -> None:
        """Configure l'apparence générale de l'application."""

        style = ttk.Style()

        try:
            style.theme_use("vista")
        except tk.TclError:
            pass

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 22, "bold"),
        )

        style.configure(
            "Subtitle.TLabel",
            font=("Segoe UI", 10),
        )

        style.configure(
            "Section.TLabelframe.Label",
            font=("Segoe UI", 11, "bold"),
        )

        style.configure(
            "Status.TLabel",
            font=("Segoe UI", 10, "bold"),
        )

        style.configure(
            "Action.TButton",
            font=("Segoe UI", 10),
            padding=(14, 9),
        )

    def _build_interface(self) -> None:
        """Construit tous les éléments de la fenêtre."""

        main_frame = ttk.Frame(
            self.root,
            padding=18,
        )
        main_frame.pack(
            fill="both",
            expand=True,
        )

        self._build_header(main_frame)
        self._build_printer_section(main_frame)
        self._build_configuration_section(main_frame)
        self._build_maintenance_section(main_frame)
        self._build_log_section(main_frame)
        self._build_status_bar()

    def _build_header(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent)
        header.pack(
            fill="x",
            pady=(0, 18),
        )

        title = ttk.Label(
            header,
            text="OpenIJ",
            style="Title.TLabel",
        )
        title.pack(anchor="w")

        subtitle = ttk.Label(
            header,
            text="Utilitaire libre et léger pour imprimantes Canon IJ",
            style="Subtitle.TLabel",
        )
        subtitle.pack(anchor="w", pady=(2, 0))

    def _build_printer_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(
            parent,
            text="Imprimante",
            padding=14,
            style="Section.TLabelframe",
        )
        frame.pack(
            fill="x",
            pady=(0, 12),
        )

        ttk.Label(
            frame,
            text="Adresse IP :",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
        )

        self.ip_entry = ttk.Entry(
            frame,
            textvariable=self.ip_var,
            width=24,
        )
        self.ip_entry.grid(
            row=0,
            column=1,
            sticky="ew",
        )

        self.test_button = ttk.Button(
            frame,
            text="Tester la connexion",
            command=self.test_connection,
            style="Action.TButton",
        )
        self.test_button.grid(
            row=0,
            column=2,
            padx=(12, 0),
        )

        ttk.Label(
            frame,
            text="État :",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(12, 0),
        )

        self.status_label = ttk.Label(
            frame,
            textvariable=self.status_var,
            style="Status.TLabel",
        )
        self.status_label.grid(
            row=1,
            column=1,
            columnspan=2,
            sticky="w",
            pady=(12, 0),
        )

        frame.columnconfigure(1, weight=1)

    def _build_configuration_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(
            parent,
            text="Configuration",
            padding=14,
            style="Section.TLabelframe",
        )
        frame.pack(
            fill="x",
            pady=(0, 12),
        )

        self.enable_quiet_button = ttk.Button(
            frame,
            text="Activer le mode silencieux",
            command=lambda: self.set_quiet_mode(True),
            style="Action.TButton",
        )
        self.enable_quiet_button.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 6),
        )

        self.disable_quiet_button = ttk.Button(
            frame,
            text="Désactiver le mode silencieux",
            command=lambda: self.set_quiet_mode(False),
            style="Action.TButton",
        )
        self.disable_quiet_button.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(6, 0),
        )

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

    def _build_maintenance_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(
            parent,
            text="Maintenance",
            padding=14,
            style="Section.TLabelframe",
        )
        frame.pack(
            fill="x",
            pady=(0, 12),
        )

        self.alignment_button = ttk.Button(
            frame,
            text="Alignement automatique",
            command=self.automatic_alignment,
            style="Action.TButton",
        )
        self.alignment_button.pack(
            fill="x",
        )

    def _build_log_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(
            parent,
            text="Journal",
            padding=10,
            style="Section.TLabelframe",
        )
        frame.pack(
            fill="both",
            expand=True,
        )

        text_frame = ttk.Frame(frame)
        text_frame.pack(
            fill="both",
            expand=True,
        )

        self.log_text = tk.Text(
            text_frame,
            height=12,
            wrap="word",
            state="disabled",
            font=("Consolas", 9),
        )
        self.log_text.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar = ttk.Scrollbar(
            text_frame,
            orient="vertical",
            command=self.log_text.yview,
        )
        scrollbar.pack(
            side="right",
            fill="y",
        )

        self.log_text.configure(
            yscrollcommand=scrollbar.set,
        )

        clear_button = ttk.Button(
            frame,
            text="Effacer le journal",
            command=self.clear_log,
        )
        clear_button.pack(
            anchor="e",
            pady=(8, 0),
        )

    def _build_status_bar(self) -> None:
        status_bar = ttk.Label(
            self.root,
            textvariable=self.activity_var,
            relief="sunken",
            anchor="w",
            padding=(8, 4),
        )
        status_bar.pack(
            side="bottom",
            fill="x",
        )

    def log(self, message: str) -> None:
        """Ajoute un message horodaté dans le journal."""

        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"

        self.log_text.configure(state="normal")
        self.log_text.insert("end", line)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _get_client(self) -> CanonClient:
        """Crée un client à partir de l'adresse IP saisie."""

        ip_address = self.ip_var.get().strip()

        if not ip_address:
            raise ValueError(
                "Veuillez saisir l'adresse IP de l'imprimante."
            )

        return CanonClient(ip_address)

    def _set_busy(self, busy: bool, activity: str = "Prêt") -> None:
        """Active ou désactive les boutons pendant une opération."""

        self.is_busy = busy
        self.activity_var.set(activity)

        state = "disabled" if busy else "normal"

        self.test_button.configure(state=state)
        self.enable_quiet_button.configure(state=state)
        self.disable_quiet_button.configure(state=state)
        self.alignment_button.configure(state=state)
        self.ip_entry.configure(state=state)

    def _run_in_thread(
        self,
        action,
        activity: str,
    ) -> None:
        """Exécute une opération réseau sans bloquer l'interface."""

        if self.is_busy:
            return

        self._set_busy(True, activity)

        thread = threading.Thread(
            target=action,
            daemon=True,
        )
        thread.start()

    def test_connection(self) -> None:
        self._run_in_thread(
            self._test_connection_worker,
            "Test de la connexion...",
        )

    def _test_connection_worker(self) -> None:
        try:
            client = self._get_client()
            self.root.after(
                0,
                self.log,
                f"Connexion à {client.ip_address}...",
            )

            response = client.get_status(
                service_type="print"
            )

            canon_response = client._get_xml_value(
                response.text,
                "response",
            )

            response_detail = client._get_xml_value(
                response.text,
                "response_detail",
            )

            if canon_response == "OK":
                status = "Connectée et disponible"
            elif response_detail == "Suspended":
                status = "Connectée, en veille"
            else:
                status = "Connectée, état inconnu"

            self.client = client

            self.root.after(
                0,
                self.status_var.set,
                status,
            )
            self.root.after(
                0,
                self.log,
                f"Imprimante détectée : {status}.",
            )

        except Exception as error:
            self.client = None

            self.root.after(
                0,
                self.status_var.set,
                "Connexion impossible",
            )
            self.root.after(
                0,
                self.log,
                f"Erreur de connexion : {error}",
            )
            self.root.after(
                0,
                messagebox.showerror,
                "OpenIJ",
                str(error),
            )

        finally:
            self.root.after(
                0,
                self._set_busy,
                False,
                "Prêt",
            )

    def set_quiet_mode(self, enabled: bool) -> None:
        action_name = (
            "Activation du mode silencieux..."
            if enabled
            else "Désactivation du mode silencieux..."
        )

        self._run_in_thread(
            lambda: self._quiet_mode_worker(enabled),
            action_name,
        )

    def _quiet_mode_worker(self, enabled: bool) -> None:
        try:
            client = self._get_client()

            self.root.after(
                0,
                self.log,
                (
                    "Activation du mode silencieux..."
                    if enabled
                    else "Désactivation du mode silencieux..."
                ),
            )

            client.set_quiet_mode(enabled)

            self.client = client

            result = (
                "Mode silencieux activé."
                if enabled
                else "Mode silencieux désactivé."
            )

            self.root.after(
                0,
                self.status_var.set,
                "Connectée",
            )
            self.root.after(
                0,
                self.log,
                result,
            )
            self.root.after(
                0,
                messagebox.showinfo,
                "OpenIJ",
                result,
            )

        except Exception as error:
            self.root.after(
                0,
                self.log,
                f"Erreur : {error}",
            )
            self.root.after(
                0,
                messagebox.showerror,
                "OpenIJ",
                str(error),
            )

        finally:
            self.root.after(
                0,
                self._set_busy,
                False,
                "Prêt",
            )

    def automatic_alignment(self) -> None:
        self._run_in_thread(
            self._automatic_alignment_worker,
            "Alignement automatique en cours...",
        )

    def _automatic_alignment_worker(self) -> None:
        try:
            client = self._get_client()

            self.root.after(
                0,
                self.log,
                "Lancement de l'alignement automatique...",
            )

            result = client.automatic_head_alignment()

            self.client = client

            message = (
                "Commande d'alignement acceptée."
            )

            if result.progress:
                message += f" Progression : {result.progress}."

            self.root.after(
                0,
                self.status_var.set,
                "Connectée",
            )
            self.root.after(
                0,
                self.log,
                message,
            )
            self.root.after(
                0,
                messagebox.showinfo,
                "OpenIJ",
                message,
            )

        except Exception as error:
            self.root.after(
                0,
                self.log,
                f"Erreur d'alignement : {error}",
            )
            self.root.after(
                0,
                messagebox.showerror,
                "OpenIJ",
                str(error),
            )

        finally:
            self.root.after(
                0,
                self._set_busy,
                False,
                "Prêt",
            )


def run_app() -> None:
    root = tk.Tk()
    OpenIJApp(root)
    root.mainloop()