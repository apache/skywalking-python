# Coding Style for SkyWalking Python

## Quotes 

As we know both single quotes and double quotes are both acceptable in Python. 
For a better coding style, we enforce a check for using single quotes when possible.

Please only use double quotes on the outside when there are inevitable single quotes inside the string, or when there
are nest quotes.

For example - 
```python
foo = f"I'm a string"
bar = f"This repo is called 'skywalking-python'"
```

Run [unify](https://github.com/myint/unify) `unify -r your_target --in-place` to fix your quotes if flake8 complaints about it.

## String formatting

Since Python 3.5 is end of life, we fully utilize the clarity and performance boost brought by [f-strings](https://docs.python.org/3/reference/lexical_analysis.html#f-strings).
Please do not use other styles - `+`, `%` or `.format` unless f-string is absolutely unfeasible in the context unless
it is a logger message, which is [optimized](https://docs.python.org/3/howto/logging.html#optimization) for the `%` style

Run [flynt](https://github.com/ikamensh/flynt) to convert other formats to f-string, pay **extra care** to possible corner 
cases leading to a semantically different conversion.

## Debug messages
Please import the `logger_debug_enabled` variable and wrap your debug messages with a check.

This should be done for all performance critical components.

```python
if logger_debug_enabled:
    logger.debug('Message - %s', some_func())
```