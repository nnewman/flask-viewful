# Flask-Viewful

Loosely inspired by [Flask-Classful](https://github.com/teracyhq/flask-classful)

### Background

After using Flask-Classful for years, I wanted to move toward
something a bit simpler. A peek under-the-hood at Flask-Classful
reveals a well-engineered method for constructing functional views out
of the class-based views defined using the package. One day, while peeking
at Flask's `View` class, I thought of a good way to encapsulate the parts of
Flask-Classful that I regularly found myself using with something that was easy
too hack and modify by peeking at the source.

### Installation

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

### Status

Currently a work-in-progress

ToDo:
  - Tests
  - More docs
