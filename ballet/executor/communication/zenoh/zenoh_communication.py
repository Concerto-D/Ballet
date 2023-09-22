import zenoh

from ballet.executor.logger.debug_logger import log_once

config = {}

CONN = "CONN"
DECONN = "DECONN"
ACTIVE = "ACTIVE"
INACTIVE = "INACTIVE"

last_msg_component_state = ""

class _ZenohSession:
    _session = None


def _get_zenoh_session() -> zenoh.session.Session:
    if _ZenohSession._session is None:
        _ZenohSession._session = zenoh.open()
    return _ZenohSession._session


def zenoh_session(func):
    """
    Décorateur permettant d'ouvrir et de fermer automatiquement une session Zenoh
    """
    def create_and_close_session(*args, **kwargs):
        session = _get_zenoh_session()
        result = func(*args, **kwargs, session=session)
        # time.sleep(0.2)
        return result

    return create_and_close_session


@zenoh_session
def get_nb_dependency_users(component_name: str, dependency_name: str, session: zenoh.session.Session = None) -> int:
    zenoh_topic = f"nb_users/{component_name}/{dependency_name}"
    res = session.get(zenoh_topic, zenoh.ListCollector())()
    int_res = int(res[0].ok.payload.decode("utf-8")) if len(res) > 0 else -1
    log_once.debug(f"Get nb dependency users on {zenoh_topic}, result: {int_res}")
    return int_res


@zenoh_session
def send_nb_dependency_users(nb: int, component_name: str, dependency_name: str, session: zenoh.session.Session = None):
    zenoh_topic = f"nb_users/{component_name}/{dependency_name}"
    log_once.debug(f"Put nb dependency users {str(nb)} on {zenoh_topic}")
    session.put(zenoh_topic, str(nb))


@zenoh_session
def get_refusing_state(component_name: str, dependency_name: str, session=None) -> int:
    zenoh_topic = f"refusing/{component_name}/{dependency_name}"
    res = session.get(zenoh_topic, zenoh.ListCollector())()
    bool_res = bool(int(res[0].ok.payload.decode("utf-8"))) if len(res) > 0 else False
    log_once.debug(f"Get refusing state on {zenoh_topic}, result: {bool_res}")
    return bool_res


@zenoh_session
def send_refusing_state(value: int, component_name: str, dependency_name: str, session=None):
    zenoh_topic = f"refusing/{component_name}/{dependency_name}"
    log_once.debug(f"Send refusing state {int(value)} on {zenoh_topic}")
    session.put(zenoh_topic, int(value))


@zenoh_session
def get_data_dependency(component_name: str, dependency_name: str, session=None):
    zenoh_topic = f"data/{component_name}/{dependency_name}"
    res = session.get(zenoh_topic, zenoh.ListCollector())()
    str_res = res[0].ok.payload.decode("utf-8") if len(res) > 0 else ""
    log_once.debug(f"Get data dependency on {zenoh_topic}, result: {str_res}")
    return str_res


@zenoh_session
def write_data_dependency(component_name: str, dependency_name: str, data, session=None):
    zenoh_topic = f"data/{component_name}/{dependency_name}"
    log_once.debug(f"Write date dependency {data} on {zenoh_topic}")
    session.put(zenoh_topic, data)


@zenoh_session
def send_syncing_conn(syncing_component: str, component_to_sync: str,  dep_provide: str, dep_use: str, action: str, session=None):
    zenoh_topic = f"{action}/{syncing_component}/{component_to_sync}/{dep_provide}/{dep_use}"
    log_once.debug(f"Send synced connection {action} on {zenoh_topic}")
    session.put(zenoh_topic, action)


@zenoh_session
def is_conn_synced(syncing_component: str, component_to_sync: str,  dep_provide: str, dep_use: str, action: str, session=None):
    zenoh_topic = f"{action}/{component_to_sync}/{syncing_component}/{dep_provide}/{dep_use}"
    result = session.get(zenoh_topic, zenoh.ListCollector())()
    if len(result) > 0:
        str_result = result[0].ok.payload.decode("utf-8")
    else:
        str_result = ""
    log_once.debug(f"Check synced connection on {zenoh_topic}, result: {str_result}")
    return str_result == action


@zenoh_session
def set_component_state(state: [ACTIVE, INACTIVE], component_name: str, reconfiguration_name: str, session=None):
    global last_msg_component_state
    if state + component_name + reconfiguration_name != last_msg_component_state:
        zenoh_topic = f"wait/{reconfiguration_name}/{component_name}"
        log_once.debug(f"Put component state {state} on {zenoh_topic}")
        session.put(zenoh_topic, state)
        last_msg_component_state = state + component_name + reconfiguration_name


@zenoh_session
def get_remote_component_state(component_name: str, reconfiguration_name: str, session=None) -> [ACTIVE, INACTIVE]:
    zenoh_topic = f"wait/{reconfiguration_name}/{component_name}"
    result = session.get(zenoh_topic, zenoh.ListCollector())()
    if len(result) > 0:
        str_result = result[0].ok.payload.decode("utf-8")
    else:
        str_result = ACTIVE
    log_once.debug(f"Wait component state on {zenoh_topic}, result: {str_result}")
    return str_result
