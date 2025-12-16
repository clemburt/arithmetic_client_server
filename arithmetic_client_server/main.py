"""CLI to run the arithmetic client/server application."""
import argparse
from multiprocessing import Process
from pathlib import Path
import time

from pydantic import BaseModel, FilePath, ValidationError

from arithmetic_client_server.client.client import ArithmeticClient
from arithmetic_client_server.server.server import ArithmeticServer


class CliArgs(BaseModel):
    """
    Pydantic model used to validate CLI arguments.

    :param FilePath file_path: Path to the file containing arithmetic operations.
    """

    file_path: FilePath


def run_server(output_file: Path) -> None:
    """
    Start the arithmetic server.

    The server runs in its own process and listens for incoming socket connections.
    It writes results to the specified output file.

    :param Path output_file: Path to write computation results

    :return: None
    """
    server = ArithmeticServer(output_file=output_file)
    server.start()


def parse_args() -> CliArgs:
    """
    Parse and validate command-line arguments using Pydantic.

    :return: Validated CLI arguments
    :rtype: CliArgs
    """
    parser = argparse.ArgumentParser(
        description="Arithmetic client/server command"
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

    - Preserve the original folder
    - Replace dots in extensions with underscores
    - Append '_results.txt' at the end

    :param Path input_path: Path to the input file

    :return: Path to the output file
    :rtype: Path

    Examples:
        - input: resources/operations_short.7z
        - output: resources/operations_short_7z_results.txt

    """
    suffix_safe = "_".join(input_path.suffixes).replace(".", "_")
    if not suffix_safe:
        # Fallback for plain files without extensions
        suffix_safe = ""
    return input_path.with_name(f"{input_path.stem}{suffix_safe}_results.txt")


def main() -> None:
    """
    Run the arithmetic client/server application.

    Steps:
        1. Parse CLI arguments and validate them using Pydantic.
        2. Build a safe output file path based on the input.
        3. Start the arithmetic server in a separate process.
        4. Give the server time to start listening.
        5. Launch the client to send the input file and receive results.
        6. Ensure server is properly terminated after client finishes.

    :return: None
    """
    cli_args: CliArgs = parse_args()
    input_path: Path = Path(cli_args.file_path)
    output_path: Path = build_output_path(input_path)

    # Start server in its own process
    server_process: Process = Process(target=run_server, args=(output_path,))
    server_process.start()

    # Give the server time to start listening
    time.sleep(1)

    try:
        # Launch client to send input file and retrieve results
        client: ArithmeticClient = ArithmeticClient()
        client.send_file(input_path, output_path)
    finally:
        # Ensure server is always terminated even if client fails
        server_process.terminate()
        server_process.join()


if __name__ == "__main__":
    main()
