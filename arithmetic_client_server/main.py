"""
Main entrypoint used by CI and Docker.

This script:
- Starts the server process
- Launches a client against it
- Executes an operations file provided as argument

The goal is to validate:
- Socket communication
- Multiprocessing lifecycle
- End-to-end correctness
"""

from multiprocessing import Process
from pathlib import Path
import time
import argparse

from pydantic import BaseModel, FilePath, ValidationError

from arithmetic_client_server.server.server import ArithmeticServer
from arithmetic_client_server.client.client import ArithmeticClient


class CliArgs(BaseModel):
    """
    Pydantic model used to validate CLI arguments.

    Attributes
    ----------
    file_path : FilePath
        Path to the file containing arithmetic operations.
    """

    file_path: FilePath


def run_server(output_file: Path) -> None:
    """
    Start the arithmetic server.

    The server runs in its own process and listens
    for incoming socket connections.
    """
    server = ArithmeticServer(output_file=output_file)
    server.start()


def parse_args() -> CliArgs:
    """
    Parse and validate command-line arguments.

    :return: Validated CLI arguments
    :rtype: CliArgs
    """
    parser = argparse.ArgumentParser(
        description="Arithmetic client/server integration runner"
    )

    parser.add_argument(
        "file_path",
        help="Path to the file containing arithmetic operations",
    )

    args = parser.parse_args()

    try:
        return CliArgs(file_path=args.file_path)
    except ValidationError as exc:
        parser.error(str(exc))


def build_output_path(input_path: Path) -> Path:
    """
    Construct a safe output file path based on the input file.

    - Preserves the original folder
    - Replaces dots in extensions with underscores
    - Appends '_results.txt' at the end

    Examples
    --------
    input: resources/operations_short.7z
    output: resources/operations_short_7z_results.txt

    :param input_path: Path to the input file
    :return: Path to the output file
    """
    suffix_safe = "_".join(input_path.suffixes).replace(".", "_")
    if not suffix_safe:  # fallback for plain .txt
        suffix_safe = ""
    return input_path.with_name(f"{input_path.stem}{suffix_safe}_results.txt")



def main() -> None:
    """
    Main function executed by CI or Docker.
    """
    cli_args = parse_args()
    input_path: Path = Path(cli_args.file_path)
    output_path: Path = build_output_path(input_path)

    # Pass output_path explicitly to the server
    server_process = Process(target=run_server, args=(output_path,))
    server_process.start()

    # Give the server time to start listening
    time.sleep(1)

    try:
        client = ArithmeticClient()
        client.send_file(input_path, output_path)
    finally:
        # Ensure the server is always stopped
        server_process.terminate()
        server_process.join()


if __name__ == "__main__":
    main()
