#!/bin/sh

echo "Creating virtual environment"
python -m venv '../venv'
echo "Virtual env created"

../venv/Scripts/python.exe -m pip install --upgrade pip
echo "Pip upgrade complete. Installing packages from requirements.txt"

while read requirement; do
  ../venv/Scripts/python.exe -m pip install $requirement
done < ../requirements.txt