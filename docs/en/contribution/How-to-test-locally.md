# How to test locally?

This guide assumes you just cloned the repo and are ready to make some changes.

After cloning the repo, make sure you also have cloned the submodule for protocol. Otherwise, run the command below. 
```
git submodule update --init
```

Please first refer to the [Developer Guide](Developer.md) to set up a development environment.

TL;DR: run ``make env``. This will create virtual environments for python and generate the protocol folder needed for the agent.

By now, you can do what you want. Let's get to the topic of how to test.

The test process requires `docker` and `docker-compose` throughout. If you haven't installed them, please install them first.

Then run ``make test``, which will generate a list of plugin versions based on the `support_matrix` variable in each Plugin and orchestrate
the tests automatically. Remember to inspect the outcomes carefully to debug your plugin.

Alternatively, you can run full tests via our GitHub action workflow on your own GitHub fork, it is usually easier since local environment can be
tricky to setup for new contributors. 

To do so, you need to fork this repo on GitHub and enable GitHub actions on your forked repo. Then, you can simply push your changes and
open a Pull Request to **the fork's** master branch. 

Note: GitHub automatically targets Pull Requests to the upstream repo, be careful when you open them to avoid accidental PRs to upstream.