def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('login', '/authentication/login')
    config.add_route('who', '/authentication/who')
    config.add_route('logout', '/authentication/logout')
    config.add_route('top', '/main/top')
    config.add_route('createFolder', '/main/folder', request_method='POST')
    config.add_route('queryFolder', '/main/folder/{id}', request_method='GET')
    config.add_route('renameFolder', '/main/folder/{id}', request_method='PUT')
    config.add_route('deleteFolder', '/main/folder/{id}', request_method='DELETE')
