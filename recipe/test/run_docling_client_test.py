# Mock transport exercises the SDK without an external service or local models.
import httpx
from docling_core.types.doc import DoclingDocument, DocItemLabel
from docling.datamodel.base_models import ConversionStatus
from docling.datamodel.service.targets import InBodyTarget
from docling.service_client import DoclingServiceClient

document = DoclingDocument(name='remote-smoke')
document.add_text(label=DocItemLabel.TEXT, text='Hello docling client')
requests = []

def handler(request):
    requests.append((request.method, request.url.path))
    if request.method == 'POST' and request.url.path == '/v1/convert/source/async':
        assert b'https://example.org/test.pdf' in request.content
        return httpx.Response(200, json={'task_id': 'smoke', 'task_type': 'convert', 'task_status': 'pending', 'task_position': 0, 'task_meta': None, 'error_message': None})
    if request.method == 'GET' and request.url.path == '/v1/status/poll/smoke':
        return httpx.Response(200, json={'task_id': 'smoke', 'task_type': 'convert', 'task_status': 'success', 'task_position': 0, 'task_meta': None, 'error_message': None})
    if request.method == 'GET' and request.url.path == '/v1/result/smoke':
        return httpx.Response(200, json={'status': 'success', 'processing_time': 0.0, 'document': {'filename': 'test.pdf', 'json_content': document.model_dump(mode='json')}})
    raise AssertionError(f'Unexpected request: {request.method} {request.url}')

with DoclingServiceClient(url='https://docling-service.invalid', status_watcher='polling') as client:
    client._http_client.close()
    client._http_client = httpx.Client(transport=httpx.MockTransport(handler))
    job = client.submit('https://example.org/test.pdf', target=InBodyTarget())
    assert job.task_id == 'smoke'
    assert job.poll().task_status == 'success'
    result = job.result()
    assert result.status == ConversionStatus.SUCCESS
    assert 'Hello docling client' in result.document.export_to_markdown()

assert ('POST', '/v1/convert/source/async') in requests
assert ('GET', '/v1/status/poll/smoke') in requests
assert ('GET', '/v1/result/smoke') in requests
print('client: submitted, polled and decoded a document offline')