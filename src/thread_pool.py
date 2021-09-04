import typing as t
import queue
import concurrent.futures
import requests

_EndType = t.NewType("_END", object)
_OnSuccessCallbacks = t.Callable[[requests.Response], None]
_OnFailCallbacks = t.Callable[[requests.RequestException], None]
_QueueType = queue.Queue[t.Tuple[
    t.Union[t.Dict[str, t.Any], _EndType],
    _OnSuccessCallbacks,
    _OnFailCallbacks
]]


class RequestPoolExecutor:
    def __init__(
        self,
        max_workers: int,
        default_args = None,
    ) -> None:
        self._es_queue: _QueueType = queue.Queue(
            maxsize=max_workers * 3
        )
        self._default_args = default_args
        self._end = _EndType(object())
        self._max_es_workers = max_workers

    def __enter__(self) -> 'RequestPoolExecutor':
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self._max_es_workers,
        )

        for _ in range(self._max_es_workers):
            self._executor.submit(self._send)

        return self

    def push(
        self,
        *,
        on_success: _OnSuccessCallbacks = lambda res: None,
        on_error: _OnFailCallbacks = lambda e: None,
        **kwargs: t.Any,
    ) -> None:
        self._es_queue.put((kwargs, on_success, on_error))

    def _send(self) -> None:
        while True:
            data, on_success, on_error = self._es_queue.get()
            if data is self._end:
                return None

            try:
                args = dict(self._default_args)
                args.update(data)
                response = requests.request(**args)
                on_success(response)
            except requests.RequestException as e:
                on_error(e)

    def __exit__(self, *args, **kwargs) -> None:
        for _ in range(self._max_es_workers):
            self._es_queue.put((self._end, lambda: None, lambda: None))

        self._executor.shutdown(wait=True)
