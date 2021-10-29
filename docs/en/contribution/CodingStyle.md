# Coding Style for SkyWalking Python

## String formatting

Since Python 3.5 is end of life, we fully utilize the clarity and performance boost brought by [f-strings](https://docs.python.org/3/reference/lexical_analysis.html#f-strings).
Please do not use other styles - `+`, `%` or `.format` unless f-string is absolutely unfeasible in the context, or
it is a logger message, which is [optimized](https://docs.python.org/3/howto/logging.html#optimization) for the `%` style

Run `make dev-fix` to invoke [flynt](https://github.com/ikamensh/flynt) to convert other formats to f-string, pay **extra care** to possible corner 
cases leading to a semantically different conversion.

### Quotes 

As we know both single quotes and double quotes are both acceptable in Python. 
For a better coding style, we enforce a check for using single quotes when possible.

Please only use double quotes on the outside when there are inevitable single quotes inside the string, or when there
are nest quotes.

For example - 
```python
foo = f"I'm a string"
bar = f"This repo is called 'skywalking-python'"
```

Run `make dev-fix` to invoke [unify](https://github.com/myint/unify) to deal with your quotes if flake8 complaints about it.

## Debug messages
Please import the `logger_debug_enabled` variable and wrap your debug messages with a check.

This should be done for all performance critical components.

```python
if logger_debug_enabled:
    logger.debug('Message - %s', some_func())
```

# Imports
Please make sure the imports are placed in a good order, or flake8-isort will notify you of the violations.

Run `make dev-fix` to automatically fix the sorting problem.

# Naming
In PEP8 convention, we are required to use snake_case as the accepted style.

However, there are special cases. For example, you are overriding/monkey-patching a method which happens to use the old style camelCase naming,
then it is acceptable to have the original naming convention to preserve context. 

Please mark the line with `# noqa` to avoid linting.
