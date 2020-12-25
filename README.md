# Flask-Viewful

Loosely inspired by [Flask-Classful](https://github.com/teracyhq/flask-classful)

### Background

After using Flask-Classful for years, I wanted to move toward
something a bit simpler. A peek under-the-hood at Flask-Classful
reveals a well-engineered method for constructing functional views out
of the class-based views defined using the package. One day, while peeking
at Flask's `View` class, I thought of a good way to encapsulate the parts of
Flask-Classful that I regularly found myself using with something that was easy
to hack and modify by peeking at the source.

#### Differences from Flask-Classful

* Only declared `@routes` and functions named as valid HTTP verbs are
  registered as view handlers. This is to be more explicit about routing and
  avoid unintended security issues related to accidental routes
* Resource representations are not supported, use `GenericView.after_request_func`
  instead.
* Subdomain as a class variable is not supported, use either a Blueprint or a
  `route_base` or `route_prefix parameter` instead.
* Before/after request functions are supported on the class only and not for
  each view handler function. This is to force per-view logic to be
  encapsulated in the view for better code readability.

### Installation

Requirements: `flask`

`$ git clone git@github.com:nnewman/flask-viewful.git`

`$ pip install -e flask-viewful`

### Usage

A workable example is in `example.py`, however this is loosely used
like so:

```python
from flask import Flask
from flask_viewful import GenericView, route

app = Flask(__name__)

class MyViewClass(GenericView):
    def index(self):
        return 'Simple GET route!'

    @route('/hello/<string:name>', methods=['POST'])
    def custom_route(self, name):
        return f'Hello {name}!'

MyViewClass.register(app)

if __name__ == '__main__':
    app.run()
```

#### How it works

Take a look first at the [Flask docs on pluggable views](https://flask.palletsprojects.com/en/1.1.x/views/)

This tool takes all the routes defined on a class and registers them as routes
on the app, which will have the app call `GenericView.dispatch_request` when
routed to. The class instance keeps an internal route map to match the inbound
request to a handler function on the class based on the route. That handler
function is then invoked, and the response returned.

### API

`flask_viewful.route(path: str, methods: Iterable[str], **options)`

Equivalent of `flask.route` decorator, to be used within an instance of
`flask-viewful.GenericView`.

#### _class_ `flask_viewful.GenericView`

   _classmethod_ `register(app_or_bp)`
   
   Registers the routes of the class onto the application or blueprint provided.
   
   _function_ `before_view_func()`
   
   Runs before the view function. Can be used to set context or perform other
   mutations based on the incoming request value. The return value is ignored.
   
   _function_ `after_view_func(response: Flask.Response, status: int = 200)`
   
   Runs after the view function, taking the response and status code as arguments.
   Can be used to mutate the response or the status code based on context. Must
   return a tuple of `class::Flask.Response` and `int`.
   
### Running Tests

This project uses pytest. To run tests, use `$ pytest tests/`

### Status

Beta! Please leave examples for any issues you run into. PRs welcome.
