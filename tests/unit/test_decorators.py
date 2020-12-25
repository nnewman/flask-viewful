from flask_viewful import route, RouteMeta


def test_route_decorator_applies_meta():

    @route('/example')
    def example_func():
        pass

    assert hasattr(example_func, 'route_meta')
    assert isinstance(example_func.route_meta, list)
    assert len(example_func.route_meta) == 1
    assert type(example_func.route_meta[0]) == RouteMeta
    assert example_func.route_meta[0] == RouteMeta(
        route_path='/example', methods=('GET',), options={}
    )


def test_route_decorator_kwargs():

    @route('/example', methods=('GET', 'POST'), opt1='some_value')
    def example_func():
        pass

    assert example_func.route_meta[0] == RouteMeta(
        route_path='/example',
        methods=('GET', 'POST'),
        options={'opt1': 'some_value'}
    )


def test_route_decorator_applied_multiple_times():

    @route('/example-get')
    @route('/example-post', methods=('POST',))
    def example_func():
        pass

    assert len(example_func.route_meta) == 2
    assert example_func.route_meta[0] == RouteMeta(
        route_path='/example-get', methods=('GET',), options={}
    )
    assert example_func.route_meta[1] == RouteMeta(
        route_path='/example-post', methods=('POST',), options={}
    )
