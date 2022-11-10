# Python Agent Meter Reporter

To enable or disable this feature, you will need to set some environment variables.

**Important Note**: Meter reporter is currently available to send in `gRPC` and `Kafka` protocol, 
`HTTP` protocol is not implemented yet (requires additional handler on SkyWalking OAP side).

## Enabling the feature (default)
```Python 
os.environ['SW_AGENT_METER_REPORTER_ACTIVE'] = 'True'
``` 
or
```bash
export SW_AGENT_METER_REPORTER_ACTIVE=True
```

## Disable the feature
```Python 
os.environ['SW_AGENT_METER_REPORTER_ACTIVE'] = 'False'
``` 
or
```bash
export SW_AGENT_METER_REPORTER_ACTIVE=False
```
## Counter
* `Counter` API represents a single monotonically increasing counter, automatic collect data and report to backend.
```python
builder = Counter.Builder('c2', CounterMode.INCREMENT, (("k1", "v1"), ("k2", "v2")))
# or this way
# builder = Counter.Builder('c2', CounterMode.INCREMENT).tag('key1', 'value1').tag('key2', 'value2')
c = builder.build()
c.increment(2)
```
### Syntactic sugars
```python
builder = Counter.Builder('c2', CounterMode.INCREMENT)
c = builder.build()

# increase Counter c by the time the with-wrapped codes consumed
with c.create_timer():
    # some codes may consume a certain time
```

```python
builder = Counter.Builder('c3', CounterMode.INCREMENT)
c = builder.build()

# increase Counter c by num once counter_decorator_test gets called
@Counter.increase(name='c3', num=2)
def counter_decorator_test():
    # some codes
```

```python
builder = Counter.Builder('c4', CounterMode.INCREMENT)
c = builder.build()

# increase Counter c by the time counter_decorator_test consumed
@Counter.timer(name='c4')
def counter_decorator_test(s):
    # some codes may consume a certain time
```

1. `Counter.Builder(name, tags)` Create a new counter builder with the meter name and optional tags.
1. `Counter.tag(key: str, value)` Mark a tag key/value pair.
1. `Counter.mode(mode: CounterMode)` Change the counter mode, RATE mode means reporting rate to the backend.
1. `Counter.increment(count)` Increment count to the `Counter`, It could be a positive value.

## Gauge
* `Gauge` API represents a single numerical value.
```python
# producer: iterable object
builder = Gauge.Builder('g1', producer, (("key", "value")))
g = Builder.build()
```
1. `Gauge.Builder(name, tags)` Create a new gauge builder with the meter name and iterable object, this iterable object need to produce numeric value.
1. `Gauge.tag(key: str, value)` Mark a tag key/value pair.
1. `Gauge.build()` Build a new `Gauge` which is collected and reported to the backend.

## Histogram
* `Histogram` API represents a summary sample observations with customize buckets.
```python
builder = Histogram.Builder('h2', [i / 10 for i in range(10)], ("key", "value"))
h = builder.build()
```
### Syntactic sugars
```python
builder = Histogram.Builder('h3', [i / 10 for i in range(10)])
h = builder.build()

# Histogram h will record the time the with-wrapped codes consumed
with h.create_timer():
    # some codes may consume a certain time
```

```python
builder = Histogram.Builder('h2', [i / 10 for i in range(10)])
h = builder.build()

# Histogram h will record the time histogram_decorator_test consumed
@Histogram.timer(name='h2')
def histogram_decorator_test(s):
    time.sleep(s)
```
1. `Histogram.Builder(name, tags)` Create a new histogram builder with the meter name and optional tags.
1. `Histogram.tag(key: str, value)` Mark a tag key/value pair.
1. `Histogram.minValue(value)` Set up the minimal value of this histogram, default is `0`.
1. `Histogram.build()` Build a new `Histogram` which is collected and reported to the backend.
1. `Histogram.addValue(value)` Add value into the histogram, automatically analyze what bucket count needs to be increment. rule: count into [step1, step2).