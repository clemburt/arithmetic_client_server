import socket
from multiprocessing import Process, Pipe, cpu_count
from arithmetic_client_server.server.worker import WorkerProcess
from arithmetic_client_server.common.logger import logger
from pathlib import Path


class ArithmeticServer:
    """
    TCP socket server handling arithmetic requests.

    - Spawns one worker process per expression
    - Writes results immediately to disk as soon as a worker finishes
    - Ensures each worker is destroyed immediately after finishing
    """


    def __init__(self, host: str = "127.0.0.1", port: int = 9000, output_file: Path = None):
        if output_file is None:
            raise ValueError("output_file must be provided")
        self.host = host
        self.port = port
        self.output_file = output_file

    def start(self) -> None:
        logger.info("Starting server on %s:%d", self.host, self.port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            logger.info("Server listening")

            conn, _ = s.accept()
            with conn, self.output_file.open("w", encoding="utf-8") as f_out:
                # Receive the entire payload
                chunks: list[bytes] = []
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)

                data = b"".join(chunks).decode().splitlines()
                # Pre-filter empty lines
                data = [line.strip() for line in data if line.strip()]

                max_workers = min(cpu_count(), len(data))
                active_workers = []

                for line_number, expr in enumerate(data, start=1):
                    # Wait if max_workers are active
                    while len(active_workers) >= max_workers:
                        for i, (proc, pipe_conn) in enumerate(active_workers):
                            if not proc.is_alive():
                                payload = pipe_conn.recv()
                                pipe_conn.close()
                                proc.join()
                                active_workers.pop(i)

                                # Write result immediately
                                if "result" in payload:
                                    f_out.write(f"{payload['expression']} = {payload['result']}\n")
                                else:
                                    f_out.write(f"{payload['expression']} -> ERROR: {payload['error']}\n")
                                f_out.flush()
                                break  # recheck after removing finished worker

                    # Create new worker
                    parent_conn, child_conn = Pipe()
                    worker = WorkerProcess(
                        conn=child_conn,
                        expression=expr,
                        line_number=line_number,
                    )
                    process = Process(target=worker.run)
                    process.start()
                    active_workers.append((process, parent_conn))

                # Collect remaining workers
                for proc, pipe_conn in active_workers:
                    payload = pipe_conn.recv()
                    pipe_conn.close()
                    proc.join()

                    if "result" in payload:
                        f_out.write(f"{payload['expression']} = {payload['result']}\n")
                    else:
                        f_out.write(f"{payload['expression']} -> ERROR: {payload['error']}\n")
                    f_out.flush()

                # Send results to client
                try:
                    conn.sendall(self.output_file.read_bytes())
                    logger.info("Results sent to client")
                except OSError as exc:
                    logger.error("Client disconnected before receiving results: %s", exc)
