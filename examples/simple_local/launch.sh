#!/usr/bin/env sh

cd $(dirname $0)
gnome-terminal --title mdbmaster -- ../../venv/bin/python do.py mdbmaster
gnome-terminal --title mdbworker0 -- ../../venv/bin/python do.py mdbworker0
gnome-terminal --title glance0 -- ../../venv/bin/python do.py glance0
gnome-terminal --title kst0 -- ../../venv/bin/python do.py kst0