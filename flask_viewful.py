from typing import Any, Dict, Iterable, Optional, Tuple, TypedDict, Union

from flask import Flask, Blueprint, request, Response
from flask.views import View
from werkzeug.exceptions import MethodNotAllowed
from werkzeug.routing import Map, MapAdapter, Rule


class RouteMeta(TypedDict):
    route_path: str
    methods: Iterable[str]
    options: Dict


route_keywords = {'index', 'get', 'post', 'put', 'patch', 'delete'}


def route(path: str, methods: Iterable[str] = ('GET',), **options):
    def decorator(func):
        meta = RouteMeta(route_path=path, methods=methods, options=options)
        func.route_meta = [meta, *getattr(func, 'route_meta', [])]
        return func
    return decorator


class ViewMeta(type):
    def __new__(
        mcs,
        name: str,
        bases: Tuple[type, ...],
        attrs: Dict[str, Any]
    ):
        url_map = Map()
        # Iterate over functions in the class
        # If the function has the `@route` decorator, then:
        #   For each `@route` definition:
        #     Add a rule for that `@route`
        for func_name, func in attrs.items():
            if meta_list := getattr(func, 'route_meta', None):
                for meta in meta_list:
                    url_map.add(Rule(
                        meta['route_path'],
                        methods=meta['methods'],
                        endpoint=func_name,
                        **meta.get('options', {})
                    ))

            # Register specially named routes that don't have `@route`
            path = '/' if func_name in {'index', 'post'} else '/id'
            if func_name in route_keywords and not hasattr(func, 'route_meta'):
                url_map.add(Rule(
                    path,
                    methods=[func_name if func_name != 'index' else 'get'],
                    endpoint=func_name
                ))

        attrs['url_map'] = url_map
        return super().__new__(mcs, name, bases, attrs)


class GenericView(View, metaclass=ViewMeta):
    route_base: Optional[str] = None
    route_prefix: Optional[str] = None

    def dispatch_request(self, **kwargs):
        prefix = self.route_prefix or ''
        base = self.route_base or ''
        path = request.url_rule.rule.lstrip(prefix).lstrip(base)
        method = request.method.lower()

        view_func, _ = self.url_map_adapter.match(path, method)

        if func := getattr(self, view_func, None):
            self.before_view_func()
            rv = func(**kwargs)
            if type(rv) != tuple:  # Flask view responses can be tuples
                rv = (rv,)
            return self.after_view_func(*rv)

        raise MethodNotAllowed()

    def before_view_func(self): pass

    def after_view_func(self, response: Response, status: int = 200):
        return response, status

    @classmethod
    def register(cls, app_or_bp: Union[Blueprint, Flask]):
        prefix = cls.route_prefix or ''
        base = cls.route_base or ''
        view = cls.as_view(cls.__name__)
        cls.url_map_adapter: MapAdapter = cls.url_map.bind('')
        _opts = {'rule', 'map', 'endpoint', 'methods', 'is_leaf', 'arguments'}
        for rule in cls.url_map.iter_rules():
            opts = {
                key: val
                for key, val in rule.__dict__.items()
                if key not in _opts and not key.startswith('_')
            }
            app_or_bp.add_url_rule(
                f'{prefix}{base}{rule.rule}',
                endpoint=f'{cls.__name__}:{rule.endpoint}',
                view_func=view,
                methods=rule.methods,
                **opts
            )
