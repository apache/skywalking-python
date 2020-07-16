Write-Output "Creating virtual environment"

& python -m venv '..\venv'

Write-Output "Virtual env created"

$PYEXE= Join-Path -Path $PSScriptRoot -ChildPath '..\venv\Scripts\python.exe'
& $PYEXE -m pip install --upgrade pip

Write-Output "Pip upgrade complete. Installing packages from requirements.txt"

foreach($package in Get-Content ..\requirements.txt) {
    & $PYEXE -m pip install $package
}
