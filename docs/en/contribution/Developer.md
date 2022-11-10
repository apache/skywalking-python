# Quick Start for Contributors

## Make and Makefile
We rely on `Makefile` to automate jobs, including setting up environments, testing and releasing.

First you need to have the `make` command available: 
```shell
# ubuntu/wsl
sudo apt-get update

sudo apt-get -y install make
```
or 
```shell
# windows powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser # Optional: Needed to run a remote script the first time

irm get.scoop.sh | iex

scoop install make
```
## Poetry 
We have migrated from basic pip to [Poetry](https://python-poetry.org/) to manage dependencies and package our project.

Once you have `make` ready, run `make env`, this will automatically install the right Poetry release, and create 
(plus manage) a `.venv` virtual environment for us based on the currently activated Python 3 version. Enjoy coding!

### Switching between Multiple Python Versions
Do not develop/test on Python < 3.7, since Poetry and some other functionalities we implement rely on Python 3.7+

If you would like to test on multiple Python versions, run the following to switch and recreate virtual environment:
#### Without Python Version Tools
```bash
poetry env use python3.x
poetry install
```

#### With Python Version Tools
```shell
pyenv shell 3.9.11
poetry env use $(pyenv which python)
poetry install
```

Or try: `virtualenvs.prefer-active-python`, which is an experimental poetry feature that can be set to `true` so that it will 
automatically follow environment.

# Next
Refer to the [Plugin Development Guide](How-to-develop-plugin.md) to learn how to build a new plugin for a library.