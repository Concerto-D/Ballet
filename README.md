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
To install Ballet, you just need to clone this current repository. 
Then, you must install requirements presented in *ballet/requirements.txt*. It can be automatically done by running 
    ```shell
    pip install -r ballet/requirements.txt
    ```
Please note that a virtual environment can be used.

Also, for the planning phase, MiniZinc must imperatively be installed. On your Linux machine, it can be done using the snap package manager. You can run the following command to install MiniZinc:
    ```shell
    sudo snap install minizinc
    ```
Verify the installation by running minizinc --version in your terminal.