from flask import Flask

from flask_viewful import GenericView, route


app = Flask(__name__)


class MyView(GenericView):
    @route('/foo')
    def foo(self):
        return 'bar', 200

    @route('/foo/<string:my_str>')
    def foo_str(self, my_str):
        return my_str, 200

    @route('/foo', methods=('POST',))
    def foo_post(self):
        return 'baz', 200


class MySecondView(GenericView):
    route_base = '/baz'

    @route('/foo')
    def foo(self):
        return 'bar', 200

    @route('/foo/<string:my_str>')
    def foo_str(self, my_str):
        return my_str, 200

    @route('/foo', methods=('POST',))
    def foo_post(self):
        return 'baz', 200


MyView.register(app)
MySecondView.register(app)

if __name__ == '__main__':
    app.run(debug=True)
