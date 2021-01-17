import pytest
import requests

BASE_URL = "https://hubapi.jina.ai/images"


def test_raw_status_code():
    r = requests.get(BASE_URL)
    assert r.status_code == requests.codes.ok


def test_all_images_are_unique():
    # This tests are we get only one version per image, so all image names should be unique (and latest)
    r = requests.get(BASE_URL)
    results = [image['docker-name'] for image in r.json()]
    assert len(results) == len(set(results))


def test_fields_in_results():
    # This tests all fields defined the aggregation pipeline are present in the result
    r = requests.get(BASE_URL, params={'n-per-page': 5})
    str_fields = ['docker-name', 'version', 'jina-version', 'docker-command', 'name', 'description', 'type',
                  'kind', 'license', 'url', 'documentation', 'author']
    list_fields = ['keywords', 'platform']

    for image in r.json():
        for str_field in str_fields:
            assert isinstance(image[str_field], str)

        for list_field in list_fields:
            assert isinstance(image[list_field], list)

        for semver in ['jina-version', 'version']:
            assert len(image[semver].split('.')) == 3

        assert image['docker-command'].startswith('docker pull')


@pytest.mark.parametrize('keywords', ['nlp', ['zarr'], ['nlp', 'images']])
def test_keywords(keywords):
    # This tests
    # - api returns only one version per image, for any keyword search
    # - api supports single & multi-valued filter for `keywords`
    # - every image returned carries at least one of the keywords
    params = {'keywords': keywords}
    r = requests.get(url=BASE_URL, params=params)
    results = [image['docker-name'] for image in r.json()]
    assert len(results) == len(set(results))
    for image in r.json():
        assert any(k in keywords for k in image['keywords'])


@pytest.mark.parametrize('keywords', ['nlp', ['zarr'], ['nlp', 'images']])
@pytest.mark.parametrize('jina_version', ['0.9.13'])
def test_keywords_with_jina_version(keywords, jina_version):
    # This tests
    # - api returns right jina version along with keywords
    params = {'keywords': keywords, 'jina-version': jina_version}
    r = requests.get(url=BASE_URL, params=params)
    results = [image['docker-name'] for image in r.json()]
    assert len(results) == len(set(results))
    for image in r.json():
        assert any(k in keywords for k in image['keywords'])
        assert image['jina-version'] == jina_version


@pytest.mark.parametrize('keywords', ['mjlsi', ['l,ld', ' vscbnd']])
def test_random_keywords(keywords):
    # This tests - api returns `No docs found`
    params = {'keywords': keywords}
    r = requests.get(url=BASE_URL, params=params)
    assert r.text == 'No docs found'


@pytest.mark.parametrize('name', ['torch', 'zarr'])
def test_name_regex(name):
    # This tests
    # - api returns only one version per image, for any name search
    # - every image returned contains `name` as a substring
    params = {'name': name}
    r = requests.get(url=BASE_URL, params=params)
    results = [image['docker-name'] for image in r.json()]
    assert len(results) == len(set(results))
    for image in r.json():
        assert name in image['docker-name']


@pytest.mark.parametrize('name', ['torch', 'zarr'])
@pytest.mark.parametrize('jina_version', ['0.9.13'])
def test_name_regex_with_jina_version(name, jina_version):
    # This tests
    # - api returns right jina version along with name
    params = {'name': name, 'jina-version': jina_version}
    r = requests.get(url=BASE_URL, params=params)
    results = [image['docker-name'] for image in r.json()]
    assert len(results) == len(set(results))
    for image in r.json():
        assert name in image['docker-name']
        assert image['jina-version'] == jina_version


@pytest.mark.parametrize('name', ['mjlsi', 'l,ld'])
def test_random_names(name):
    # This tests - api returns `No docs found`
    params = {'name': name}
    r = requests.get(url=BASE_URL, params=params)
    assert r.text == 'No docs found'


@pytest.mark.parametrize('kind', ['encoder', 'indexer'])
def test_kind(kind):
    # This tests
    # - api returns only one version per image, for any name search
    # - every image returned contains `name` as a substring
    params = {'kind': kind}
    r = requests.get(url=BASE_URL, params=params)
    results = [image['docker-name'] for image in r.json()]
    assert len(results) == len(set(results))
    for image in r.json():
        assert kind == image['kind']


@pytest.mark.parametrize('kind', ['encoder', 'indexer'])
@pytest.mark.parametrize('jina_version', ['0.9.13'])
def test_kind_with_jina_version(kind, jina_version):
    # This tests
    # - api returns right jina version along with name
    params = {'kind': kind, 'jina-version': jina_version}
    r = requests.get(url=BASE_URL, params=params)
    results = [image['docker-name'] for image in r.json()]
    assert len(results) == len(set(results))
    for image in r.json():
        assert kind == image['kind']
        assert image['jina-version'] == jina_version


@pytest.mark.parametrize('kind', ['mjlsi', 'l,ld'])
def test_random_kind(kind):
    # This tests - api returns `No docs found`
    params = {'kind': kind}
    r = requests.get(url=BASE_URL, params=params)
    assert r.text == 'No docs found'


@pytest.mark.parametrize('type', ['pod'])
def test_type(type):
    # This tests
    # - api returns only one version per image, for any name search
    # - every image returned contains `name` as a substring
    params = {'type': type}
    r = requests.get(url=BASE_URL, params=params)
    results = [image['docker-name'] for image in r.json()]
    assert len(results) == len(set(results))
    for image in r.json():
        assert type == image['type']


@pytest.mark.parametrize('type', ['pod'])
@pytest.mark.parametrize('jina_version', ['0.9.13'])
def test_type_with_jina_version(type, jina_version):
    # This tests
    # - api returns right jina version along with name
    params = {'type': type, 'jina-version': jina_version}
    r = requests.get(url=BASE_URL, params=params)
    results = [image['docker-name'] for image in r.json()]
    assert len(results) == len(set(results))
    for image in r.json():
        assert type == image['type']
        assert image['jina-version'] == jina_version


@pytest.mark.parametrize('type', ['mjlsi', 'l,ld'])
def test_random_type(type):
    # This tests - api returns `No docs found`
    params = {'type': type}
    r = requests.get(url=BASE_URL, params=params)
    assert r.text == 'No docs found'


@pytest.mark.parametrize('n', [5, 10])
def test_n_per_page_count(n):
    # This tests `n-per-page` query sends only `n` results
    params = {'n-per-page': n}
    r = requests.get(url=BASE_URL, params=params)
    assert len(r.json()) == n


@pytest.mark.parametrize('n', [5, 10])
def test_n_per_page_same_results_multiple_exec(n):
    # This tests - executing `n-per-page` query multiple times results the same set
    params = {'n-per-page': n}
    r = requests.get(url=BASE_URL, params=params)
    results1 = r.json()

    r = requests.get(url=BASE_URL, params=params)
    results2 = r.json()

    assert results1 == results2


@pytest.mark.parametrize('n', [5, 10, 20])
def test_pagination(n):
    r = requests.get(url=BASE_URL)
    total_images = len(r.json())

    pagination_image_count = 0
    params = {'n-per-page': n}
    r = requests.get(url=BASE_URL, params=params)
    last_docker_name = r.json()[-1]['docker-name']

    while True:
        pagination_image_count += len(r.json())
        last_docker_name = r.json()[-1]['docker-name']
        params = {'n-per-page': n, 'after': last_docker_name}
        r = requests.get(url=BASE_URL, params=params)
        if r.status_code == requests.codes.bad:
            assert r.text == 'No docs found'
            break

    assert total_images == pagination_image_count


@pytest.mark.parametrize('n', [5, 10, 20])
def test_pagination_with_filter(n):
    params = {'kind': 'encoder'}
    r = requests.get(url=BASE_URL, params=params)
    total_images = len(r.json())

    pagination_image_count = 0
    params = {'kind': 'encoder', 'n-per-page': n}
    r = requests.get(url=BASE_URL, params=params)
    last_docker_name = r.json()[-1]['docker-name']

    while True:
        pagination_image_count += len(r.json())
        last_docker_name = r.json()[-1]['docker-name']
        params = {'kind': 'encoder', 'n-per-page': n, 'after': last_docker_name}
        r = requests.get(url=BASE_URL, params=params)
        if r.status_code == requests.codes.bad:
            assert r.text == 'No docs found'
            break

    assert total_images == pagination_image_count
