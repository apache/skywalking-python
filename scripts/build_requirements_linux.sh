#!/bin/sh

echo "Building requirements.txt"

../venv/Scripts/python -m pip freeze > ../requirements.txt

echo "requirements.txt created"