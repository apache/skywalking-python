# How to use with Odoo?

The Odoo integration is intended for Odoo applications that start their own server process, such as an Odoo project
launched from a `start` script under Docker, Kubernetes, or Supervisor.

Add the SkyWalking Odoo bootstrap before the first `import odoo` in the application entrypoint:

```python
from skywalking.bootstrap.odoo import maybe_start
maybe_start()

import odoo
```

The bootstrap starts the SkyWalking agent only when both environment variables are non-empty:

```shell
SW_AGENT_NAME=odoo-service
SW_AGENT_COLLECTOR_BACKEND_SERVICES=http://oap:12800
```

`SW_AGENT_NAME` is the SkyWalking service name, following the same service naming configuration used by the other
SkyWalking Python plugins.
`SW_AGENT_COLLECTOR_BACKEND_SERVICES` is the OAP HTTP collector address. Values with `http://` and `https://`
prefixes are accepted; `https://` enables TLS for the agent's HTTP reporter. Use the OAP HTTP port, usually `12800`,
not the gRPC port `11800`.

For Docker or Kubernetes, put the two variables in the container environment. If either variable is absent or empty,
`maybe_start()` returns without starting the agent and Odoo runs normally.

The bootstrap is fail-open. If the SkyWalking agent fails to start, `maybe_start()` returns `False` and the Odoo
process can continue without tracing.
