import traceback
from functools import wraps

import yaml
from flask import Flask, request
from threading import Thread

from ballet.executor import global_variables
from ballet.executor.logger.debug_logger import log, log_once
from ballet.executor.communication.rest.rest_communication import ACTIVE, INACTIVE
import logging

# TODO: refacto with rest_communication
CONN = "CONN"
DECONN = "DECONN"


def run_api_in_thread(assembly):
    thread = Thread(target=run_flask_api, args=(assembly,))
    thread.setDaemon(True)  # Required to make the program exit when main thread exit
    thread.start()


def catch_exceptions(func):
    """
    Permet de catcher les exceptions des routes TODO: comprendre pk need de les catcher explicitement
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            log.exception(e)
            traceback.print_exc()

    return wrapper


def run_flask_api(assembly):
    app = Flask(__name__)

    @app.route("/get_nb_dependency_users/<component_name>/<dependency_name>")
    @catch_exceptions
    def get_nb_dependency_users(component_name: str, dependency_name: str):
        return str(assembly.components[component_name].st_dependencies[dependency_name].nb_users)

    @app.route("/get_refusing_state/<component_name>/<dependency_name>")
    @catch_exceptions
    def get_refusing_state(component_name: str, dependency_name: str):
        return str(assembly.components[component_name].st_dependencies[dependency_name].is_refusing)

    @app.route("/get_data_dependency/<component_name>/<dependency_name>")
    @catch_exceptions
    def get_data_dependency(component_name: str, dependency_name: str):
        return str(assembly.components[component_name].st_dependencies[dependency_name].data)

    @app.route("/is_conn_synced/<syncing_component>/<component_to_sync>/<dep_to_sync>/<syncing_dep>/<action>")
    @catch_exceptions
    def is_conn_synced(syncing_component: str, component_to_sync: str, dep_to_sync: str, syncing_dep: str, action: str):
        for conn in set(assembly.component_connections[component_to_sync]):
            use, provide = (conn.get_use_dep(), conn.get_provide_dep())
            if (use.get_component_name() in [component_to_sync, syncing_component]
                and provide.get_component_name() in [component_to_sync, syncing_component]
                and use.get_name() in [dep_to_sync, syncing_dep]
                and provide.get_name() in [dep_to_sync, syncing_dep]):
                return str(action == CONN)
        return str(action == DECONN)

    @app.route("/get_remote_component_state/<component_name>")
    @catch_exceptions
    def get_remote_component_state(component_name: str):
        calling_assembly_name = request.args.get("calling_assembly_name")
        if assembly.is_component_idle(component_name):
            assembly.remote_confirmations.add(calling_assembly_name)
            component_state = INACTIVE
        else:
            component_state = ACTIVE
        # log_once.debug(f"Remote asembly {calling_assembly_name} checks for my local state of {component_name}: {component_state}")

        return component_state

    # Remove logging of each HTTP transactions
    werkzeug_log = logging.getLogger('werkzeug')
    werkzeug_log.setLevel(logging.ERROR)

    with open(global_variables.get_inventory_absolute_path()) as f:
        loaded_inventory = yaml.safe_load(f)
    _, port = loaded_inventory[assembly.get_name()].split(":")

    app.run(host='0.0.0.0', port=port)
