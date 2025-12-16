"""Test class ArithmeticClient."""
import socket
import tarfile
import zipfile

import py7zr
from pydantic import ValidationError
import pytest

from arithmetic_client_server.client.client import ArithmeticClient


def test_client_valid_config() -> None:
    """Check that a valid host and port correctly initialize the client."""
    client = ArithmeticClient(host="127.0.0.1", port=9000)
    assert str(client.host) == "127.0.0.1"
    assert client.port == 9000


def test_client_invalid_ip() -> None:
    """Ensure invalid IP addresses raise a ValidationError."""
    with pytest.raises(ValidationError):
        ArithmeticClient(host="999.999.999.999", port=9000)


def test_client_invalid_port() -> None:
    """Ensure ports outside valid range raise a ValidationError."""
    with pytest.raises(ValidationError):
        ArithmeticClient(host="127.0.0.1", port=70000)

def test_send_file_txt(tmp_path, monkeypatch) -> None:
    """Verify sending a plain text file writes expected results to output."""
    input_file = tmp_path / "ops.txt"
    output_file = tmp_path / "results.txt"

    input_file.write_text("1+1\n2*2\n")

    # Fake socket
    class FakeSocket:
        def __init__(self):
            self.calls = 0

        def connect(self, addr):
            pass

        def sendall(self, data):
            assert b"1+1" in data

        def shutdown(self, how):
            pass

        def recv(self, size):
            self.calls += 1
            if self.calls == 1:
                return b"2\n4\n"
            return b""

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(socket, "socket", lambda *a, **kw: FakeSocket())

    client = ArithmeticClient()
    client.send_file(input_file, output_file)

    assert output_file.read_text() == "2\n4\n"

def test_extract_zip(tmp_path) -> None:
    """Check that a .zip archive can be extracted and read correctly."""
    txt = tmp_path / "ops.txt"
    txt.write_text("3+3\n")

    zip_path = tmp_path / "ops.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(txt, arcname="ops.txt")

    client = ArithmeticClient()
    content = client._extract_archive(zip_path)

    assert content == "3+3\n"

def test_extract_tar_xz(tmp_path) -> None:
    """Check that a .tar.xz archive can be extracted and read correctly."""
    txt = tmp_path / "ops.txt"
    txt.write_text("4*4\n")

    tar_path = tmp_path / "ops.tar.xz"
    with tarfile.open(tar_path, "w:xz") as tf:
        tf.add(txt, arcname="ops.txt")

    client = ArithmeticClient()
    content = client._extract_archive(tar_path)

    assert content == "4*4\n"

def test_extract_7z(tmp_path) -> None:
    """Check that a .7z archive can be extracted and read correctly."""
    txt = tmp_path / "ops.txt"
    txt.write_text("5-2\n")

    archive_path = tmp_path / "ops.7z"
    with py7zr.SevenZipFile(archive_path, "w") as archive:
        archive.write(txt, arcname="ops.txt")

    client = ArithmeticClient()
    content = client._extract_archive(archive_path)

    assert content == "5-2\n"

def test_extract_archive_no_txt(tmp_path) -> None:
    """Verify that extraction fails if no .txt file exists in the archive."""
    zip_path = tmp_path / "empty.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("data.bin", b"\x00\x01")

    client = ArithmeticClient()

    with pytest.raises(ValueError):
        client._extract_archive(zip_path)

def test_extract_unsupported_format(tmp_path) -> None:
    """Ensure unsupported archive formats raise a ValueError."""
    file_path = tmp_path / "ops.rar"
    file_path.write_text("1+1")

    client = ArithmeticClient()

    with pytest.raises(ValueError):
        client._extract_archive(file_path)
