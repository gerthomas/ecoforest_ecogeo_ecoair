"""ecoAIR client: register/coil reads plus a handful of strictly validated control writes."""
import asyncio
import logging
import string
from datetime import datetime, timezone

import httpx
from pyecoforest.api import EcoforestApi
from pyecoforest.exceptions import (
    EcoforestAuthenticationRequired,
    EcoforestConnectionError,
    EcoforestError,
)

from ..ecoair_controls import (
    CONTROLS, WRITE_REGISTER_OPERATION, encode_control, parse_write, validate_write)
from ..ecoair_map import ecoair_register_mapping
from ..registers import (
    decode, parse_read, read_requests, signed_integer, split_optional_request, validate_read)
from .device import EcoGeoDevice

_LOGGER = logging.getLogger(__name__)

MODEL_ADDRESS = 5323
MODEL_LENGTH = 6
OP_GET = {1: 2002, 2: 2001}  # data_type 1 = registers, 2 = coils


class ControlsDisabledError(EcoforestError):
    """Raised when a write is attempted without opting in to controls."""


class EcoAirApi(EcoforestApi):
    """Reads the documented ecoAIR table; writes only the whitelisted controls, only if allowed."""

    def __init__(self, host: str, user: str, password: str, allow_control: bool = False) -> None:
        super().__init__(host, httpx.BasicAuth(user, password))
        self.mapping = ecoair_register_mapping()
        self.allow_control = allow_control
        self._model_name = None
        self._lock = asyncio.Lock()

    async def _request(self, data=None):
        is_write = isinstance(data, dict) and data.get('idOperacion') == WRITE_REGISTER_OPERATION
        if is_write:
            validate_write(data)
            if not self.allow_control:
                raise ControlsDisabledError('Controls are disabled for this entry')
        else:
            validate_read(data)
        try:
            response = await self._client.post(
                '/recepcion_datos_4.cgi', auth=self._auth,
                timeout=self._timeout, data=data,
            )
            response.raise_for_status()
            if is_write:
                parse_write(response.text)
                return None
            return parse_read(response.text, data)
        except httpx.HTTPStatusError as err:
            if err.response.status_code in (401, 403):
                raise EcoforestAuthenticationRequired(err.response.status_code) from err
            raise EcoforestConnectionError('Ecoforest HTTP request failed') from err
        except (httpx.RequestError, ValueError) as err:
            raise EcoforestConnectionError('Invalid or failed Ecoforest request') from err

    async def _load_data(self, address, length, op_type):
        values = await self._request({'idOperacion': op_type, 'dir': address, 'num': length})
        return dict(zip(range(address, address + length), values))

    async def get(self) -> EcoGeoDevice:
        async with self._lock:
            return await self._get()

    async def _get(self):
        if self._model_name is None:
            data = await self._load_data(MODEL_ADDRESS, MODEL_LENGTH, 2002)
            symbols = ['--'] + list(string.digits + string.ascii_uppercase)
            codes = [signed_integer(data[a]) for a in range(MODEL_ADDRESS, MODEL_ADDRESS + MODEL_LENGTH)]
            if any(n < 0 or n >= len(symbols) for n in codes):
                raise EcoforestConnectionError('Invalid Ecoforest model code')
            self._model_name = ''.join(symbols[n] for n in codes)
        requests = read_requests(self.mapping)
        state = {1: {}, 2: {}}
        errors = []
        index = 0
        while index < len(requests):
            request = requests[index]
            index += 1
            attempts = 1 if request['optional'] else 3
            for attempt in range(attempts):
                try:
                    state[request['data_type']].update(await self._load_data(
                        request['address'], request['length'], OP_GET[request['data_type']]))
                    break
                except EcoforestAuthenticationRequired:
                    raise
                except EcoforestConnectionError:
                    if attempt + 1 < attempts:
                        await asyncio.sleep(2 ** attempt)
                    elif request['optional']:
                        smaller = split_optional_request(request)
                        if smaller:
                            requests[index:index] = smaller
                        else:
                            errors.append((request['data_type'], request['address'], request['length']))
                    else:
                        raise
            await asyncio.sleep(0.05)
        if not state[1] and not state[2]:
            raise EcoforestConnectionError('No register block could be read')
        values, raw_values = {}, {}
        for key, definition in self.mapping.items():
            raw = state[definition['data_type']].get(definition['address'])
            raw_values[key] = raw
            values[key] = decode(raw, definition)
        return EcoGeoDevice.build(self._model_name, values, raw_values=raw_values,
                                  failed_reads=errors, observed_at=datetime.now(timezone.utc).isoformat())

    async def write_control(self, key: str, value) -> None:
        """Write one whitelisted control and log if the read-back differs."""
        control = CONTROLS.get(key)
        if control is None:
            raise ValueError('Unknown control')
        if not self.allow_control:
            raise ControlsDisabledError('Controls are disabled for this entry')
        address, hexvalue = encode_control(control, value)
        async with self._lock:
            await self._request({'idOperacion': WRITE_REGISTER_OPERATION, 'dir': address, 'num': 1,
                                 hexvalue: hexvalue})
            await asyncio.sleep(0.2)
            readback = (await self._load_data(address, 1, 2002))[address]
        if readback.upper() != hexvalue:
            _LOGGER.warning('Control %s: wrote %s but read back %s', key, hexvalue, readback)

    async def async_close(self):
        await self._client.aclose()
