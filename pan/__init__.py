from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator

from .utils.security import groupfinder


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    authz_policy = ACLAuthorizationPolicy()
    config.set_authorization_policy(authz_policy)
    # Enable JWT authentication.
    config.include('pyramid_jwt')
    config.set_jwt_authentication_policy('secret', http_header='pToken')
    config.include('pyramid_jinja2')
    config.include('.models')
    config.include('.routes')
    config.scan()
    return config.make_wsgi_app()
