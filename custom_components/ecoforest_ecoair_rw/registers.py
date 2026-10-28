"""Register read/decode helpers (no Home Assistant imports). Writes live in ecoair_controls.py."""
import re

READ_OPERATIONS = {2001, 2002}
MAX_READ_LENGTH = 64


def validate_read(data):
    """Reject writes, arbitrary payloads and oversized requests before network I/O."""
    if not isinstance(data, dict) or set(data) != {'idOperacion', 'dir', 'num'}:
        raise ValueError('Only register/coil reads are permitted')
    if any(type(data[k]) is not int for k in data):
        raise ValueError('Read operation, address and count must be integers')
    if data['idOperacion'] not in READ_OPERATIONS:
        raise ValueError('Ecoforest client is read-only')
    if not (0 <= data['dir'] <= 65535 and 1 <= data['num'] <= 125
            and data['dir'] + data['num'] <= 65536):
        raise ValueError('Invalid register range')


def parse_read(response, request):
    """Validate read status, echoed range, exact payload length and encoding."""
    validate_read(request)
    lines = response.strip().splitlines()
    header = 'error_geo_get_bit=0' if request['idOperacion'] == 2001 else 'error_geo_get_reg=0'
    if len(lines) != 3 or lines[0].strip() != header or lines[2].strip() != '0':
        raise ValueError('Invalid or rejected Ecoforest read response')
    parts = lines[1].strip().split('&')
    if parts[:2] != [f"dir={request['dir']}", f"num={request['num']}"]:
        raise ValueError('Ecoforest response address/count mismatch')
    values = parts[2:]
    pattern = r'[01]' if request['idOperacion'] == 2001 else r'[0-9a-fA-F]{4}'
    if len(values) != request['num'] or any(not re.fullmatch(pattern,v) for v in values):
        raise ValueError('Invalid Ecoforest read payload')
    return values


def signed_integer(raw):
    n = int(raw,16)
    return n - 65536 if n >= 32768 else n


def read_requests(mapping):
    """Read only named addresses, serially; optional failures never mask core reads."""
    requests=[]
    for dt in [2,1]:
        rows=sorted((r for r in mapping.values() if r['data_type']==dt),key=lambda r:r['address'])
        current=None
        for r in rows:
            optional=r.get('optional',False)
            if (current and r['address']==current['address']+current['length']
                    and current['optional']==optional and current['length']<MAX_READ_LENGTH):
                current['length']+=1
            else:
                current=dict(address=r['address'],length=1,data_type=dt,optional=optional)
                requests.append(current)
    return requests


def split_optional_request(request):
    """Bisect a rejected optional block so supported neighbours remain available."""
    if not request.get('optional') or request['length'] <= 1:
        return []
    left_length = request['length'] // 2
    return [
        dict(request, length=left_length),
        dict(request, address=request['address'] + left_length,
             length=request['length'] - left_length),
    ]


def decode(raw, definition):
    if raw is None:
        return None
    if definition['data_type']==2:
        return int(raw)
    n=signed_integer(raw)
    if 'valid_values' in definition and n not in definition['valid_values']:
        return None
    if 'enum' in definition:
        return definition['enum'].get(str(n))
    value=n*definition.get('scale',1)+definition.get('offset',0)
    if definition['entity_type']=='temperature' and n==-9999:
        return None
    return round(value,6) if isinstance(value,float) else value
