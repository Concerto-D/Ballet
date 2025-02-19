# Ballet choreography tool

## Introduction
Welcome to Ballet. This README provides a view of the project architecture, and instructions on how to set up and use the prototype on your machine. Please follow the steps below to ensure a smooth installation and usage experience.

## Architecture
Ballet is composed of 7 modules
- **gateway** which contains the code of the gateway, aiming at parsing input files and share goals among the nodes
- **planner** which contains the code for planning a reconfiguration, including the communication protocol and the use of CP solving techniques (MiniZinc support)
- **executor** which contains the code for running a plan on an assembly
- **assembly** which proposes models for defining assemblies. A simplified model is also provided, and is used by the planner
- **support** which contains some supportive functions for usage
- **utils** which contains basic functions on datastructures
- **test** which contains some unit tests that were used for debugging
In addition, *choreography.py* contains some high-level functions for conducting each step of the global choreography.

## Installation

Ballet is not yet on pypi so to install Ballet, you first need to clone the repository:
```sh
$ git clone git@github.com:Concerto-D/Ballet.git
$ cd Ballet
```

all packages installation will be local to your installation. To do that you need to create a virtual env:
```sh
$ python -m venv

$ venv/bin/activate
```

After which you may run standard commands: `python` to execute, `pip` to install, etc... If `venv/bin/activate` didn't work you may run commands not from your global installation but from the virtual environment:
```sh
$ venv/bin/python # execute

$ venv/bin/pip # install package
```

As a prerequisite to make Ballet work you will need [concerto](https://github.com/Concerto-D/concerto-decentralized). It is also not published on pypi so not easily installable but can be retrieved thus:
```sh
$ git clone git@github.com:Concerto-D/concerto-decentralized.git /path/to/concerto-d
$ venv/bin/pip install /path/to/concerto-d
```

After that, it's the standard procedure:
```sh
venv/bin/pip install .
```

# If activate doesn't work
venv/bin/pip install .
```

Also, for the planning phase, MiniZinc must imperatively be installed. The apt version on Ubuntu 24.04 is not up to date, prefer the edge versino from snap:
```sh
$ sudo snap install minizinc
```
Verify the installation by running minizinc --version in your terminal.

## Usage

See the examples in the (examples)[./examples] folder

## Development

To run all tests:

```sh
venv/bin/python -m unittest discover
```