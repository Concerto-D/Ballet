# Ballet & Ballet⁺

## Installation

To run Ballet and Ballet⁺, follow these steps:

1. To install Ballet, you just need to clone this current repository and install using standard procedure:

    ```shell
    cd Ballet

    python -m venv venv
    venv/bin/activate

    pip install .

    # If activate doesn't work
    venv/bin/pip install .
    ```

2. Build the personalized Choco solver using make. Ensure that Maven is installed beforehand:

```sh
sudo apt install maven  # On Linux
make
```

3. Install minizinc. On ubuntu, it can be done using the snap package manager:
    ```shell
    sudo snap install minizinc
    ```
Verify the installation by running minizinc --version in your terminal.

## Development

To run all tests:

	```shell
	venv/bin/python -m unittest discover
	```

## Overview

The `balletplus` module contains all the extensions we made. It enhances Ballet’s planner by introducing conflict management capabilities.

## Examples

Example usage can be found in the `examples/` directory.
