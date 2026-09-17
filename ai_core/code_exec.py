"""
code_exec — a Python execution tool so agents do EXACT math and data/spreadsheet
analysis (the way ChatGPT's Code Interpreter does). The model writes short Python;
Python computes on the data; only the small result returns → accurate AND token-cheap.

Files ingested via the API are written into the executor's working directory, so the
model can `pd.read_excel("report.xlsx")` / `pd.read_csv("sales.csv")` by filename.

⚠️ SECURITY: this runs real Python in a subprocess with a timeout and a stripped env,
but it is NOT a hardened sandbox. For untrusted/multi-tenant use, run it inside a
locked-down container or a dedicated low-privilege user / gVisor / firecracker.
"""
import asyncio
import os
import tempfile

from .config import Config

CODE_EXEC_SCHEMA = {
    "type": "function",
    "function": {
        "name": "code_exec",
        "description": (
            "Run Python for EXACT calculations, number-crunching, and data/spreadsheet "
            "analysis. pandas and numpy are available. Files the user uploaded are in the "
            "current working directory — read them by filename (e.g. pd.read_excel('pnl.xlsx'), "
            "pd.read_csv('sales.csv')). ALWAYS print() the results you want back. "
            "Use this instead of doing arithmetic yourself."
        ),
        "parameters": {
            "type": "object",
            "properties": {"code": {"type": "string", "description": "Python code; print() outputs."}},
            "required": ["code"],
        },
    },
}


class CodeExec:
    def __init__(self, workdir: str = None, timeout: int = 15):
        self.workdir = workdir or tempfile.mkdtemp(prefix="ai_core_exec_")
        os.makedirs(self.workdir, exist_ok=True)
        self.timeout = timeout
        self.files = []

    def add_file(self, filename: str, data: bytes) -> str:
        name = os.path.basename(filename or "file")
        path = os.path.join(self.workdir, name)
        with open(path, "wb") as f:
            f.write(data)
        if name not in self.files:
            self.files.append(name)
        return name

    async def run(self, code: str) -> dict:
        proc = await asyncio.create_subprocess_exec(
            "python", "-I", "-c", code,
            cwd=self.workdir,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            env={"PATH": os.environ.get("PATH", ""), "HOME": self.workdir},
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return {"ok": False, "error": f"code_exec timed out after {self.timeout}s"}
        return {
            "ok": proc.returncode == 0,
            "stdout": out.decode("utf-8", errors="ignore")[-4000:],
            "stderr": err.decode("utf-8", errors="ignore")[-2000:],
        }


def code_exec_tool(executor: CodeExec):
    """Returns (schema, impls) to attach to agents."""
    async def _impl(code: str):
        return await executor.run(code)
    return CODE_EXEC_SCHEMA, {"code_exec": _impl}
