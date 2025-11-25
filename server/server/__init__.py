"""
Server components: HTTP request handler, lifecycle, and utilities.

Import submodules directly to avoid circular dependencies:
    from server.handler import MockRequestHandler
    from server.lifecycle import create_server, setup_reload_watcher
    from server.utils import CaseInsensitiveDict, is_port_available
"""
