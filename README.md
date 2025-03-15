# Ballet & Ballet⁺

## Installation

To run Ballet and Ballet⁺, follow these steps:

1. Install the required Python dependencies:

```sh
python -m pip install -r requirements.txt
```

2. Build the personalized Choco solver using make. Ensure that Maven is installed beforehand:

```sh
sudo apt install maven  # On Linux
make
```

## Overview

The `balletplus` module contains all the extensions we made. It enhances Ballet’s planner by introducing conflict management capabilities.

## Examples

Example usage can be found in the `examples/` directory.