echo "Building requirements.txt"

..\venv\Scripts\python.exe -m pip freeze > ..\requirements.txt

echo "requirements.txt created"