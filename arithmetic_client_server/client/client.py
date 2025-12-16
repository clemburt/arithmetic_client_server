"""TCP client."""
from pathlib import Path
import socket
import tarfile
import tempfile
import zipfile

import py7zr
from pydantic import BaseModel, ConfigDict, Field, FilePath, IPvAnyAddress


class ArithmeticClient(BaseModel):
    """
    TCP client responsible for sending arithmetic operations to the server and receiving computed results.

    The TCP client:
    - reads arithmetic expressions from a plain text file or an archive
    - sends raw expressions to the server over a TCP socket
    - receives computed results from the server
    - writes results into an output file
    """

    # Make the Pydantic instance immutable (read-only), to prevent errors
    # that could be caused by changes to the network configuration during execution.
    model_config = ConfigDict(frozen=True)

    host: IPvAnyAddress = Field(default="127.0.0.1", description="Server host address")
    port: int = Field(default=9000, ge=1, le=65535, description="Server TCP port")


    def send_file(self,
        input_file: FilePath,
        output_file: FilePath,
    ) -> None:
        """
        Send an input file containing arithmetic expressions to the server and write the computed results to an output file.
        
        :param FilePath input_file: Path to the input file or archive
        :param FilePath output_file: Path where results will be written
        
        :return: None
        :raises ValueError: If the archive format is unsupported or contains no .txt file
        """
        # Load expressions from file or archive
        if input_file.suffix == ".txt":
            # Plain text file: read directly
            content = input_file.read_text()
        else:
            # Archive file: extract the first text file found
            content = self._extract_archive(input_file)

        # Open a TCP socket to the server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Establish connection
            s.connect((self.host, self.port))
            # Send all expressions to the server
            s.sendall(content.encode())
            # Signal that no more data will be sent
            s.shutdown(socket.SHUT_WR)
            
            # Receive computed results from the server
            with output_file.open("w", encoding="utf-8") as f_out:
                while True:
                    # Read up to 4096 bytes from the socket
                    # recv() returns:
                    # - a non-empty bytes object when data is available
                    # - an empty bytes object (b"") when the peer has closed the connection
                    # Note: chunks are small pieces of data read from a TCP stream, as data may arrive in multiple packets
                    chunk = s.recv(4096)
                    # No more data means the server finished sending the response
                    if not chunk:
                        break
                    # Decode the received bytes chunk into a UTF-8 string and append it to the output file
                    # Flushing forces the data to be written to disk immediately, ensuring progress is not lost
                    # if the process is interrupted (e.g. KeyboardInterrupt or crash)
                    f_out.write(chunk.decode())
                    f_out.flush()

    def _extract_archive(self, archive_path: FilePath) -> str:
        """
        Extract the first .txt file found in a supported archive and return its content as a string.

        Supported formats:
        - .zip
        - .tar.xz
        - .7z

        :param FilePath archive_path: Path to the archive file
        
        :return: Content of the extracted .txt file
        :rtype: str
        :raises ValueError: If no .txt file is found or format is unsupported
        """
        # Create a temporary directory for safe extraction
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            if archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path, "r") as zf:
                    txt_files = [f for f in zf.namelist() if f.endswith(".txt")]
                    if not txt_files:
                        raise ValueError("📄❌ No .txt file found in zip archive")
                    zf.extract(txt_files[0], path=tmpdir_path)
                    return (tmpdir_path / txt_files[0]).read_text()

            elif archive_path.suffixes[-2:] == [".tar", ".xz"] or archive_path.suffix == ".tar.xz":
                with tarfile.open(archive_path, "r:xz") as tf:
                    txt_files = [m for m in tf.getmembers() if m.name.endswith(".txt")]
                    if not txt_files:
                        raise ValueError("📄❌ No .txt file found in tar.xz archive")
                    tf.extract(txt_files[0], path=tmpdir_path, filter="data")
                    return (tmpdir_path / txt_files[0].name).read_text()

            elif archive_path.suffix == ".7z":
                with py7zr.SevenZipFile(archive_path, mode="r") as archive:
                    txt_files = [f for f in archive.getnames() if f.endswith(".txt")]
                    if not txt_files:
                        raise ValueError("📄❌ No .txt file found in 7z archive")
                    archive.extract(targets=[txt_files[0]], path=tmpdir_path)
                    return (tmpdir_path / txt_files[0]).read_text()

            else:
                raise ValueError(f"📄❌ Unsupported archive format: {archive_path.suffix}")
