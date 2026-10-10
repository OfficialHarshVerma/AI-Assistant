import subprocess
import time
import urllib.request
from pathlib import Path
import sys

class LlamaServerManager:

    def __init__(self):

        if getattr(sys, "frozen", False):
            self.project_folder = Path(sys.executable).resolve().parent
        else:
            self.project_folder = Path(__file__).resolve().parent
        self.llama_exe = (
            self.project_folder
            / "llama"
            / "llama-server.exe"
        )

        self.model_file = (
            self.project_folder
            / "models"
            / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
        )

        self.process = None

    def start(self):

        if self.process is not None:
            return

        if not self.llama_exe.exists():
            raise FileNotFoundError(
                f"llama-server.exe not found:\n{self.llama_exe}"
            )

        if not self.model_file.exists():
            raise FileNotFoundError(
                f"Qwen model not found:\n{self.model_file}"
            )

        print("Starting local Qwen server...")

        command = [
            str(self.llama_exe),
            "-m",
            str(self.model_file),
            "--host",
            "127.0.0.1",
            "--port",
            "8080"
        ]

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        print("Waiting for Qwen server...")

        for _ in range(60):

            if self.is_ready():
                print("Qwen server is ready.")
                return

            time.sleep(1)

        self.stop()

        raise RuntimeError(
            "Qwen server failed to start."
        )

    def is_ready(self):

        try:

            urllib.request.urlopen(
                "http://127.0.0.1:8080/v1/models",
                timeout=1
            )

            return True

        except Exception:

            return False

    def stop(self):

        if self.process is None:
            return

        print("Stopping Qwen server...")

        try:

            self.process.terminate()
            self.process.wait(timeout=5)

        except Exception:

            try:
                self.process.kill()
            except Exception:
                pass

        self.process = None

        print("Qwen server stopped.")