# Python Agent Meter Reporter

To enable or disable this feature, you will need to set some environment variables.


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
tg_ls = [MeterTag("key", "value")]
c = Counter('c2', CounterMode.INCREMENT, tg_ls)
# or with more compact way
# Counter('c2', CounterMode.INCREMENT).tag('key1', 'value1').tag('key2', 'value2')
c.build()
c.increment(2)
```
### Syntactic sugars
```python
c = Counter('c2', CounterMode.INCREMENT)
c.build()

# increase Counter c by the time the with-wrapped codes consumed
with c.create_timer():
    # some codes may consume a certain time
```

```python
c = Counter('c3', CounterMode.INCREMENT)
c.build()

# increase Counter c by num once counter_decorator_test gets called
@Counter.increase(name='c3', num=2)
def counter_decorator_test():
    # some codes
```

```python
c = Counter('c4', CounterMode.INCREMENT)
c.build()

# increase Counter c by the time counter_decorator_test consumed
@Counter.timer(name='c4')
def counter_decorator_test(s):
    # some codes may consume a certain time
```

1. `Counter(name, tags)` Create a new counter with the meter name and optional tags.
1. `Counter.tag(key: str, value)` Mark a tag key/value pair.
1. `Counter.mode(mode: CounterMode)` Change the counter mode, RATE mode means reporting rate to the backend.
1. `Counter.increment(count)` Increment count to the `Counter`, It could be a positive value.

## Gauge
* `Gauge` API represents a single numerical value.
```python
tg_ls = [MeterTag("key", "value")]
# producer: iterable object
g = Gauge('g1', producer, tg_ls)
g.build()
```
1. `Gauge(name, tags)` Create a new gauge with the meter name and iterable object, this iterable object need to produce numeric value.
1. `Gauge.tag(key: str, value)` Mark a tag key/value pair.
1. `Gauge.build()` Build a new `Gauge` which is collected and reported to the backend.

## Histogram
* `Histogram` API represents a summary sample observations with customize buckets.
```python
tg_ls = [MeterTag("key", "value")]
h = Histogram('h2', [i / 10 for i in range(10)], tg_ls)
h.build()
```
### Syntactic sugars
```python
h = Histogram('h3', [i / 10 for i in range(10)])
h.build()

# Histogram h will record the time the with-wrapped codes consumed
with h.create_timer():
    # some codes may consume a certain time
```

```python
h = Histogram('h2', [i / 10 for i in range(10)])
h.build()

# Histogram h will record the time histogram_decorator_test consumed
@Histogram.timer(name='h2')
def histogram_decorator_test(s):
    time.sleep(s)
```
1. `Histogram(name, tags)` Create a new histogram with the meter name and optional tags.
1. `Histogram.tag(key: str, value)` Mark a tag key/value pair.
1. `Histogram.minValue(value)` Set up the minimal value of this histogram, default is `0`.
1. `Histogram.build()` Build a new `Histogram` which is collected and reported to the backend.
1. `Histogram.addValue(value)` Add value into the histogram, automatically analyze what bucket count needs to be increment. rule: count into [step1, step2).