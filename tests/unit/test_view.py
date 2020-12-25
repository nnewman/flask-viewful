from typing import Set

import pytest
from flask import Blueprint, Flask, g, url_for
from flask_viewful import GenericView, route


class MyGenericView(GenericView):
    @route('/example')
    def example(self):
        return 'ok'

    @route('/example/<string:my_str>')
    def example_args(self, my_str: str):
        return my_str

    @route('/', methods=('POST',))
    def post(self):
        return 'ok'

    def get(self, id):
        return id


@pytest.fixture()
def app():
    bp = Blueprint('my_bp', __name__, url_prefix='/bp-prefix')

    @bp.route('/unrelated-route')
    def unrelated_route():
        return 'ok'

    app = Flask(__name__)

    MyGenericView.register(bp)
    MyGenericView.register(app)
    app.register_blueprint(bp)

    return app


def _assert_routes_in_rules(app, path: str, methods: Set[str]):
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    assert path in routes
    assert routes.count(path) == 1  # test that it's applied once
    rule = list(app.url_map.iter_rules())[routes.index(path)]
    assert rule.methods == methods


def test_special_routes_applied(app):
    # test `post`
    _assert_routes_in_rules(app, '/', {'POST', 'OPTIONS'})

    # test `get`
    _assert_routes_in_rules(app, '/<id>', {'GET', 'HEAD', 'OPTIONS'})

    # test `example`
    _assert_routes_in_rules(app, '/example', {'GET', 'HEAD', 'OPTIONS'})

    # test `example/my_str`
    _assert_routes_in_rules(
        app, '/example/<string:my_str>', {'GET', 'HEAD', 'OPTIONS'}
    )


def test_blueprint_prefix_applies(app):
    # test `post`
    _assert_routes_in_rules(app, '/bp-prefix/', {'POST', 'OPTIONS'})

    # test `get`
    _assert_routes_in_rules(app, '/bp-prefix/<id>', {'GET', 'HEAD', 'OPTIONS'})

    # test `example`
    _assert_routes_in_rules(
        app, '/bp-prefix/example', {'GET', 'HEAD', 'OPTIONS'}
    )

    # test `example/my_str`
    _assert_routes_in_rules(
        app, '/bp-prefix/example/<string:my_str>', {'GET', 'HEAD', 'OPTIONS'}
    )


def test_routing_with_blueprint_and_prefix():
    bp = Blueprint('my_bp', __name__, url_prefix='/bp-prefix')

    class MyGenericViewWithPrefix(MyGenericView):
        route_prefix = '/view-prefix'

    MyGenericViewWithPrefix.register(bp)
    app = Flask(__name__)
    app.register_blueprint(bp)

    # test `post`
    _assert_routes_in_rules(
        app, '/bp-prefix/view-prefix/', {'POST', 'OPTIONS'}
    )

    # test `get`
    _assert_routes_in_rules(
        app, '/bp-prefix/view-prefix/<id>', {'GET', 'HEAD', 'OPTIONS'}
    )

    # test `example`
    _assert_routes_in_rules(
        app, '/bp-prefix/view-prefix/example', {'GET', 'HEAD', 'OPTIONS'}
    )

    # test `example/my_str`
    _assert_routes_in_rules(
        app,
        '/bp-prefix/view-prefix/example/<string:my_str>',
        {'GET', 'HEAD', 'OPTIONS'}
    )


def test_routing_with_blueprint_prefix_and_base():
    bp = Blueprint('my_bp', __name__, url_prefix='/bp-prefix')

    class MyGenericViewWithPrefix(MyGenericView):
        route_prefix = '/view-prefix'
        route_base = '/view-base'

    MyGenericViewWithPrefix.register(bp)
    app = Flask(__name__)
    app.register_blueprint(bp)

    # test `post`
    _assert_routes_in_rules(
        app, '/bp-prefix/view-prefix/view-base/', {'POST', 'OPTIONS'}
    )

    # test `get`
    _assert_routes_in_rules(
        app,
        '/bp-prefix/view-prefix/view-base/<id>',
        {'GET', 'HEAD', 'OPTIONS'}
    )

    # test `example`
    _assert_routes_in_rules(
        app,
        '/bp-prefix/view-prefix/view-base/example',
        {'GET', 'HEAD', 'OPTIONS'}
    )

    # test `example/my_str`
    _assert_routes_in_rules(
        app,
        '/bp-prefix/view-prefix/view-base/example/<string:my_str>',
        {'GET', 'HEAD', 'OPTIONS'}
    )


def test_multiple_inheritance():
    app = Flask(__name__)

    class LevelOneInherit(MyGenericView):
        @route('/level-one')
        def level_one(self):
            return 'ok'

    class LevelTwoInherit(LevelOneInherit):
        @route('/level-two')
        def level_two(self):
            return 'ok'

    LevelTwoInherit.register(app)  # Only register double-inherited view

    _assert_routes_in_rules(app, '/example', {'GET', 'HEAD', 'OPTIONS'})
    _assert_routes_in_rules(app, '/level-one', {'GET', 'HEAD', 'OPTIONS'})
    _assert_routes_in_rules(app, '/level-two', {'GET', 'HEAD', 'OPTIONS'})


def test_before_view_function():
    app = Flask(__name__)

    class MyBeforeFuncView(GenericView):
        def before_view_func(self):
            g.my_var = 'example'

        def index(self):
            return g.my_var

    MyBeforeFuncView.register(app)

    with app.test_client() as client:
        assert client.get('/').data == b'example'


def test_after_view_function():
    app = Flask(__name__)

    class MyAfterFuncView(GenericView):
        def after_view_func(self, response, status):
            response += ' world!'
            status_code = 201
            return response, status_code

        def index(self):
            return 'hello', 200

    MyAfterFuncView.register(app)

    with app.test_client() as client:
        resp = client.get('/')
        assert resp.data == b'hello world!'
        assert resp.status_code == 201


def test_url_for():
    app = Flask(__name__)

    class MyExampleView(GenericView):
        @route('/example')
        def example(self):
            return 'ok'

        def index(self):
            return 'hello', 200

    MyExampleView.register(app)
    app.config['SERVER_NAME'] = 'example.com'

    with app.app_context():
        assert url_for('MyExampleView:example') == 'http://example.com/example'
        assert url_for('MyExampleView:index') == 'http://example.com/'


def test_match_for_blueprint(app):
    with app.test_client() as client:
        resp = client.get('/bp-prefix/example')
        assert resp.status_code == 200
        assert resp.data == b'ok'
