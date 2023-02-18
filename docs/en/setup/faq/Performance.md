# Performance best practices
> Following changes are expected in the next official release (v1.1.0).

The Python agent currently uses a number of threads to communicate with SkyWalking OAP, 
it is planned to be refactored using AsyncIO (Uvloop) along with an async version of 
gRPC(aio-client)/HTTP(aiohttp/httpx)/Kafka(aio-kafka) to further minimize the cost of thread switching and IO time. 

**For now, we still have a few points to mention to keep the overhead to your application minimal.**

1. When using the gRPC protocol to report data, a higher version of gRPC is always recommended. Please also make sure that:
   1. By running `python -c "from google.protobuf.internal import api_implementation; print(api_implementation._implementation_type)"`,
    or `python -c "from google.protobuf.internal import api_implementation; print(api_implementation._default_implementation_type)"`
   you should either see `upb` or `cpp` as the returned value. It means the Protobuf library is using a much faster implementation than Python native.
   If not, try setting `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION='cpp' or 'upb'` or upgrade the gRPC dependency (SkyWalking Python will use whatever version your application uses).
2. Though HTTP is provided as an alternative, it could be slower compared to other protocols, Kafka is often a good choice when gRPC is not suitable.
3. When some features are not needed in your use case, you could turn them off either via 
`config.init(agent_some_reporter_active=False)` or environment variables.
4. Use ignore_path, ignore_method, and log filters to avoid reporting less valuable data that is of large amount.
5. Log reporter safe mode is designed for situations where HTTP basic auth info could be visible in traceback and logs but shouldn't be reported to OAP. 
You should keep the option as OFF if it's not your case because frequent regular expression searches will inevitably introduce overhead to the CPU.
6. Do not turn on `sw-python` CLI or agent debug logging in production, otherwise large amount of log will be produced.
   1. sw-python CLI debug mode will automatically turn on agent debug log (override from `sitecustomize.py`).