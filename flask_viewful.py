from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional, Tuple, Union

from flask import Flask, Blueprint, request, Response
from flask.views import View
from werkzeug.exceptions import MethodNotAllowed
from werkzeug.routing import Map, MapAdapter, Rule


@dataclass
class RouteMeta:
    route_path: str
    methods: Iterable[str]
    options: Dict = field(default_factory=dict)


route_keywords = {'index', 'get', 'post', 'put', 'patch', 'delete'}


def _lstrip(text: str, chars: str) -> str:
    """
    Given a string `text`, remove the leading `chars` if and only if they
    appear as the leading characters
    """
    if chars and text[:len(chars)] == chars:
        text = text[len(chars):]
    return text


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

        # For bases, take the attrs that were not overridden and re-add them
        # so they get processed
        for base in bases:
            if base_map := getattr(base, 'url_map', None):  # type: Map
                for rule in base_map.iter_rules():
                    if rule.endpoint not in attrs:
                        attrs[rule.endpoint] = getattr(base, rule.endpoint)

        # Iterate over functions in the class
        # If the function has the `@route` decorator, then:
        #   For each `@route` definition:
        #     Add a rule for that `@route`
        for func_name, func in attrs.items():
            if meta_list := getattr(func, 'route_meta', None):
                for meta in meta_list:  # type: RouteMeta
                    url_map.add(Rule(
                        meta.route_path,
                        methods=meta.methods,
                        endpoint=func_name,
                        **meta.options
                    ))

            # Register specially named routes that don't have `@route`
            path = '/' if func_name in {'index', 'post'} else '/<id>'
            if func_name in route_keywords and not hasattr(func, 'route_meta'):
                url_map.add(Rule(
                    path,
                    methods=['get' if func_name == 'index' else func_name],
                    endpoint=func_name
                ))

        attrs['url_map'] = url_map
        return super().__new__(mcs, name, bases, attrs)


class GenericView(View, metaclass=ViewMeta):
    route_base: Optional[str] = None
    route_prefix: Optional[str] = None

    _bp_prefix: Optional[str] = None  # Placeholder for prefix on the BP

    def dispatch_request(self, **kwargs):
        bp_prefix = self._bp_prefix or ''
        prefix = self.route_prefix or ''
        base = self.route_base or ''
        path = _lstrip(request.url_rule.rule, bp_prefix)  # strip bp_prefix
        path = _lstrip(path, prefix)  # strip class prefix
        path = _lstrip(path, base)  # strip route base
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
        # If the blueprint has a url_prefix, stash it on the class
        if isinstance(app_or_bp, Blueprint):
            cls._bp_prefix = app_or_bp.url_prefix

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
            if 'defaults' in opts and opts['defaults'] is None:
                del opts['defaults']
            app_or_bp.add_url_rule(
                f'{prefix}{base}{rule.rule}',
                endpoint=f'{cls.__name__}:{rule.endpoint}',
                view_func=view,
                methods=rule.methods,
                **opts
            )
