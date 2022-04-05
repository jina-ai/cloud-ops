import asyncio
import os
from contextlib import suppress
from enum import Enum
from functools import partial
from http import HTTPStatus
from typing import Dict, List, Optional

import aiohttp
from jina.helper import colored, get_or_reuse_loop
from jina.logging.logger import JinaLogger

cyaned = partial(colored, color='cyan')
default_logger = JinaLogger('🐺 WOLF')

os.environ['JINA_LOG_LEVEL'] = 'DEBUG'
WOLF_API = 'https://api.wolf.jina.ai/dev/flows'
LOGSTREAM_API = 'wss://logs.wolf.jina.ai/dev/'
headers = {'Authorization': os.environ['WOLF_TOKEN']}


def validate_id(id: str, kind='jflow'):
    assert id.startswith(kind), f'Invalid ID passed, doesn\'t start with `{kind}`'
    assert (
        len(id.split(f'{kind}-')[-1]) == 10
    ), f'Invalid ID passed, len(id) is not `10`'


def validate_flow_id(id):
    validate_id(id, 'jflow')


def validate_workspace_id(id):
    validate_id(id, 'jworkspace')


class Status(str, Enum):
    SUBMITTED = 'SUBMITTED'
    STARTING = 'STARTING'
    FAILED = 'FAILED'
    ALIVE = 'ALIVE'
    UPDATING = 'UPDATING'
    DELETING = 'DELETING'
    DELETED = 'DELETED'

    def streamable(self) -> bool:
        return self in (Status.ALIVE, Status.UPDATING, Status.DELETING)

    def alive(self) -> bool:
        return self == Status.ALIVE

    def deleted(self) -> bool:
        return self == Status.DELETED


class WolfFlow:
    def __init__(
        self,
        filepath: Optional[str] = None,
        name: Optional[str] = None,
        workspace: Optional[str] = None,
        flow_id: Optional[str] = None,
        logstream: bool = False,
    ) -> None:
        self.filepath = filepath
        self.name = name
        self.workspace = workspace
        self.flow_id: Optional[str] = flow_id
        self.enable_logstream = logstream
        self.host: Optional[str] = None
        self.gateway: Optional[str] = None
        self.loop = get_or_reuse_loop()

    async def deploy(self):
        with open(self.filepath) as f:
            params = {}
            if self.name is not None:
                params['name'] = self.name
            if self.workspace is not None:
                params['workspace'] = self.workspace

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=WOLF_API,
                    data={'yaml': f},
                    params=params,
                    headers=headers,
                ) as response:
                    json_response = await response.json()
                    assert (
                        response.status == HTTPStatus.CREATED
                    ), f'Got Invalid response status {response.status}, expected {HTTPStatus.CREATED}'
                    if self.name is not None:
                        assert self.name in json_response['name']
                    assert Status(json_response['status']) == Status.SUBMITTED
                    self.flow_id: str = json_response['id']
                    self.workspace: str = json_response['workspace']
                    self.c_logstream_task = asyncio.create_task(
                        WolfFlow.logstream({'request_id': json_response['request_id']})
                    )
                    self.host = f'{self.name}-{self.flow_id.split("-")[1]}.wolf.jina.ai'
                    default_logger.info(
                        f'POST /flows with flow_id {cyaned(self.flow_id)} & '
                        f'request_id {cyaned(json_response["request_id"])} ..'
                    )
                    return json_response

    @staticmethod
    async def fetch(flow_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=f'{WOLF_API}/{flow_id}') as response:
                json_response = await response.json()
                assert (
                    response.status == HTTPStatus.OK
                ), f'Got Invalid response status {response.status}, expected {HTTPStatus.OK}'
                return json_response

    async def fetch_until(
        self,
        intermediate: List[Status],
        desired: Status = Status.ALIVE,
    ):
        count = 0
        while count < 100:
            json_response = await WolfFlow.fetch(self.flow_id)
            if Status(json_response['status']) == desired:
                gateway = json_response["gateway"]
                default_logger.success(
                    f'Successfully reached status: {desired} with gateway {gateway}'
                )
                return gateway
            else:
                current_status = Status(json_response['status'])
                assert current_status in intermediate
                default_logger.debug(
                    f'current status is {current_status}, sleeping for 10secs'
                )
                await asyncio.sleep(10)
                count += 1

    async def terminate(self):
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                url=f'{WOLF_API}/{self.flow_id}',
                headers=headers,
            ) as response:
                json_response = await response.json()
                assert (
                    response.status == HTTPStatus.ACCEPTED
                ), f'Got Invalid response status {response.status}, expected {HTTPStatus.ACCEPTED}'
                self.t_logstream_task = asyncio.create_task(
                    WolfFlow.logstream(
                        params={'request_id': json_response['request_id']}
                    )
                )
                assert json_response['id'] == str(self.flow_id)
                assert Status(json_response['status']) == Status.DELETING

    @staticmethod
    async def logstream(params):
        default_logger.debug(f'Asked to stream logs with params {params}')
        try:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.ws_connect(LOGSTREAM_API, params=params) as ws:
                        default_logger.success(
                            f'Successfully connected to logstream API with params: {params}'
                        )
                        await ws.send_json({})
                        async for msg in ws:
                            if msg.type == aiohttp.http.WSMsgType.TEXT:
                                log_dict: Dict = msg.json()
                                if log_dict.get('status') == 'STREAMING':
                                    print(log_dict['message'])
                    default_logger.debug(f'Disconnected from the logstream server ...')
                except aiohttp.WSServerHandshakeError as e:
                    default_logger.critical(
                        f'Couldn\'t connect to the logstream server as {e!r}'
                    )
        except asyncio.CancelledError:
            default_logger.debug(f'logstream task cancelled.')
        except Exception as e:
            default_logger.error(f'Got an exception while streaming logs {e!r}')

    async def __aenter__(self):
        await self.deploy()
        self.gateway = await self.fetch_until(
            intermediate=[Status.SUBMITTED, Status.STARTING],
            desired=Status.ALIVE,
        )
        await self.c_logstream_task
        if self.enable_logstream:
            self.logstream_task = self.loop.create_task(
                WolfFlow.logstream(params={'flow_id': str(self.flow_id)})
            )
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.terminate()
        await self.fetch_until(
            intermediate=[Status.DELETING],
            desired=Status.DELETED,
        )
        await self.t_logstream_task
        await WolfFlow.cancel_pending()

    @staticmethod
    async def cancel_pending():
        for task in asyncio.all_tasks():
            task.cancel()
            with suppress(asyncio.CancelledError, RuntimeError):
                await task

    def __enter__(self):
        return self.loop.run_until_complete(self.__aenter__())

    def __exit__(self, *args, **kwargs):
        self.loop.run_until_complete(self.__aexit__(*args, **kwargs))
