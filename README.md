# Ballet & Ballet⁺

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
