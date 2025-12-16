# Table of Contents
- [Purpose](#purpose)
  - [Input files](#input-files)
  - [The server receives information using TCP sockets](#the-server-receives-information-using-tcp-sockets)
  - [The application is built by different processes](#the-application-is-built-by-different-processes)
  - [Processes lifecycle is monitored](#processes-lifecycle-is-monitored)
  - [Arithmetic operations are performed securely](#arithmetic-operations-are-performed-securely)
  - [Logger](#logger)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Tests](#tests)
- [Documentation](#documentation)
- [License](#license)
- [Authors](#authors)

# Purpose

**arithmetic_client_server** is a Python socket-based client/server application using multiprocessing and pipes to safely compute arithmetic operations from files

This application complies with the following guidelines:

## Input files

The input file which contains the arithmetic operations to perform must be a text file, compressed or not

The supported input file formats are: .txt, .zip, .tar.xz, .7z

Here is an example of an input file:

```text
38 - 83 - 52 + 30 - 24 - 89 / 66 + 18 / 7 * 77
57 + 87 - 24 * 27 / 8 + 53 - 87 * 6 * 60 - 30
63 * 23 - 91 - 17 * 45 + 63 * 52 - 50
47 - 88 + 32 - 71 * 39 * 68
43 * 47 - 75 + 94 * 35 - 60 + 55 + 8
49 - 97 + 17 + 31 / 37 + 82
74 - 36 - 96 + 32 + 2 + 26
43 - 45 - 66 - 52 - 6
41 / 50 + 53 + 40
```

Here is an example of the resulting output file:

```text
38 - 83 - 52 + 30 - 24 - 89 / 66 + 18 / 7 * 77 = 105.65151515151518
57 + 87 - 24 * 27 / 8 + 53 - 87 * 6 * 60 - 30 = -31234.0
63 * 23 - 91 - 17 * 45 + 63 * 52 - 50 = 3819.0
47 - 88 + 32 - 71 * 39 * 68 = -188301.0
43 * 47 - 75 + 94 * 35 - 60 + 55 + 8 = 5239.0
49 - 97 + 17 + 31 / 37 + 82 = 51.83783783783784
74 - 36 - 96 + 32 + 2 + 26 = 2.0
43 - 45 - 66 - 52 - 6 = -126.0
41 / 50 + 53 + 40 = 93.82
```

## The server receives information using TCP sockets

The application uses a single TCP connection between client and server for data exchange, while all parallel computation and inter-process communication are handled using multiprocessing and pipes, ensuring a clear separation between networking and computation

The application uses 2 TCP sockets:
- one listening socket on the server
- and one active client-server connection socket

## The application is built by different processes

- A main parent process, launched by the main to start the server (`server_process`)
- A parent server process (`ArithmeticServer.start`) that accepts the connection, listens on the socket, orchestrates the workers and writes the results as they come in
- A child worker process for each arithmetic operation (`WorkerProcess`), created dynamically for each line in the file, which sends the result via a `Pipe` and is immediately destroyed by the server after completion

Therefore, the total number of active processes at any given time depends on the number of simultaneous workers, limited by `max_workers`:

```python
max_workers = min(cpu_count(), len(data))
```

## Processes lifecycle is monitored

Child worker processes communicate their results to the server through multiprocessing pipes, which provide safe (minimum API, no explicit synchronisation with lock and semaphore) and simple (no shared memory) inter-process communication

The parent server process creates and destroys each child worker process after it computed its arithmetic operation and sent the result

Multiprocessing is used:
- instead of threading to bypass the Python Global Interpreter Lock (GIL), required by arithmetic operations which are executed as bytecode instructions, and to achieve true CPU parallelism (because GIL would only allow one thread at a time to execute bytecode)
- while avoiding pools to maintain strict control over workers creation and destruction, because pools recycle workers for multiple tasks and automatically manage the lifecycle of processes

## Arithmetic operations are performed securely

The `eval()` method has been prohibited because it would allow arbitrary Python code execution from untrusted client input, which is unacceptable in a networked multiprocessing server:
- this Remote Code Execution (RCE) could lead to the execution of system commands, data leaks, total server compromise, etc.
- there would be no validation of arithmetic operators, because anything that is syntactically valid would be accepted, not just `+`, `-`, `*`, and `/`
- the server would be less robust in the event of an `eval()` command failure, which could raise various exceptions that are difficult to debug

## Logger

In this multiprocessing client/server application, using structured logging instead of console `print()` ensures clear, timestamped, process-safe, and level-specific output, making debugging and monitoring reliable across multiple worker processes

# Architecture

```text
┌──────────────────────────────┐
│          CLI / CI            │
│        (main.py)             │
│                              │
│  - parse arguments           │
│  - build output_path         │
│  - start server process      │
└──────────────┬───────────────┘
               │
               │ multiprocessing.Process
               ▼
┌──────────────────────────────┐
│     Server Process           │
│  (ArithmeticServer)          │
│                              │
│  TCP LISTEN SOCKET           │
│  bind(host, port)            │
│  listen()                    │
│                              │
│  accept()                    │
│       │                      │
│       ▼                      │
│  TCP CONNECTION SOCKET       │◄───────────────┐
│                              │                │
│  - receive operations        │                │
│  - orchestrate workers       │                │
│  - write results to file     │                │
│                              │                │
└──────────────┬───────────────┘                │
               │                                │
               │ multiprocessing.Pipe           │
               │                                │
               ▼                                │
┌──────────────────────────────┐                │
│     Worker Process #1        │                │
│                              │                │
│  - compute ONE expression    │                │
│  - send result via Pipe      │                │
│  - terminate immediately     │                │
└──────────────────────────────┘                │
               │                                │
               ▼                                │
        (many workers in parallel)              │
               │                                │
               ▼                                |
┌──────────────────────────────┐                │
│     Worker Process #N        │                │
│                              │                │
│  - compute ONE expression    │                │
│  - send result via Pipe      │                │
│  - terminate immediately     │                │
└──────────────────────────────┘                │
                                                │
┌──────────────────────────────┐                │
│        Client Process        │────────────────┘
│     (ArithmeticClient)       │
│                              │
│  TCP CLIENT SOCKET           │
│  connect(host, port)         │
│                              │
│  - send operations file      │
│  - receive results file      │
│  - write output file         │
└──────────────────────────────┘
```

# Installation
Make sure you have [PDM](https://pdm.fming.dev/) installed

```bash
pdm install
```

If running inside Docker, you can use the published image:

```bash
docker pull ghcr.io/clemburt/arithmetic_client_server:latest
```

# Usage
You can use the CLI either locally or from the Docker container

```bash
sekoia --help
```

Output:

```bash
usage: sekoia [-h] file_path

Arithmetic client/server integration runner

positional arguments:
  file_path   Path to the file containing arithmetic operations

options:
  -h, --help  show this help message and exit
```

Example:

```bash
sekoia ./arithmetic_client_server/resources/operations.txt
```

# Tests
Run the test suite using:
```bash
pdm install -dG test
pdm test
```

The Docker image installs only production dependencies (--prod), so tests must be run explicitly with test group install:

```bash
docker run --rm \
  ghcr.io/clemburt/arithmetic_client_server:latest \
  sh -c "pdm install -dG test && pdm test"
```

This will:
- Sync test dependencies
- Run all tests with coverage reporting

# Documentation
Build the sphinx documentation using
```bash
pdm install -dG doc
pdm doc
```

The Docker image installs only production dependencies (--prod), so doc must be run explicitly with doc group install:

```bash
docker run --rm \
  ghcr.io/clemburt/arithmetic_client_server:latest \
  sh -c "pdm install -dG doc && pdm doc"
```

📚 [Documentation](https://clemburt.github.io/arithmetic_client_server/)

# License
MIT License

# Authors
- [BURTSCHER Clément](https://github.com/clemburt)
