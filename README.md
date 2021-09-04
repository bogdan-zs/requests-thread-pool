# requests-thread-pool
Parallel sync requests.
## Example
```py
with RequestPoolExecutor(
    max_workers=100,
    default_args={'method': 'GET', 'url': 'https://httpbin.org/get', 'params': {'a': 1}}
) as executor:
    for _ in range(100):
        executor.push(
            on_success=lambda res: print(res.text),
            on_error=lambda err: print(err),
            params={'a': 123}
        )
```