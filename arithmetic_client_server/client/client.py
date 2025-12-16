import socket
from pathlib import Path
import tempfile
import zipfile
import tarfile
import py7zr  # pip install py7zr


class ArithmeticClient:
    """
    TCP client responsible for sending arithmetic operations to the server
    and receiving computed results.

    Workflow:
    - Read operations from a file or archive
    - Send raw expressions through a socket
    - Receive results from the server
    - Persist results into an output file
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 9000):
        self.host = host
        self.port = port

    def send_file(self, input_file: Path, output_file: Path) -> None:
        # Determine file type
        if input_file.suffix == ".txt":
            # Plain text file
            content = input_file.read_text()
        else:
            # Archive: extract first text file
            content = self._extract_archive(input_file)

        # Send to server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.sendall(content.encode())
            s.shutdown(socket.SHUT_WR)
            result = s.recv(65536).decode()
            output_file.write_text(result)

    def _extract_archive(self, archive_path: Path) -> str:
        """
        Extracts the first .txt file from supported archives and returns its content as string.
        Supports: .zip, .tar.xz, .7z
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            if archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path, "r") as zf:
                    txt_files = [f for f in zf.namelist() if f.endswith(".txt")]
                    if not txt_files:
                        raise ValueError("No .txt file found in zip archive")
                    zf.extract(txt_files[0], path=tmpdir_path)
                    return (tmpdir_path / txt_files[0]).read_text()

            elif archive_path.suffixes[-2:] == [".tar", ".xz"] or archive_path.suffix == ".tar.xz":
                with tarfile.open(archive_path, "r:xz") as tf:
                    txt_files = [m for m in tf.getmembers() if m.name.endswith(".txt")]
                    if not txt_files:
                        raise ValueError("No .txt file found in tar.xz archive")
                    tf.extract(txt_files[0], path=tmpdir_path)
                    return (tmpdir_path / txt_files[0].name).read_text()

            elif archive_path.suffix == ".7z":
                with py7zr.SevenZipFile(archive_path, mode="r") as archive:
                    txt_files = [f for f in archive.getnames() if f.endswith(".txt")]
                    if not txt_files:
                        raise ValueError("No .txt file found in 7z archive")
                    archive.extract(targets=[txt_files[0]], path=tmpdir_path)
                    return (tmpdir_path / txt_files[0]).read_text()

            else:
                raise ValueError(f"Unsupported archive format: {archive_path.suffix}")
