import os
import time
from datetime import datetime

import yaml

# from concerto import global_variables
# from concerto.debug_logger import log, log_once

from ballet.executor.logger.debug_logger import log, log_once
from ballet.executor import global_variables

LOG_DIR_TIMESTAMP = ""
ASSEMBLY_NAME = ""
TIMESTAMP_EXPE_START = 0.0


all_timestamps_dict = {}


def create_timestamp_metric(timestamp_type, is_instruction_method=False):
    """
    If the node raise Exception saying it goes to sleep, then take the measure and
    exit the program
    """
    def _create_timestamp_metric(func):
        def wrapper(*args, **kwargs):
            if not is_instruction_method:
                log_args, log_kwargs = (), {}
            else:
                current_instruction_num = str(global_variables.current_nb_instructions_done)
                log_args, log_kwargs = (current_instruction_num, *args[1:]), dict(kwargs)   # args[1:] to ignore self

            log_time_value(timestamp_type, TimestampPeriod.START, *log_args, **log_kwargs)
            result = func(*args, **kwargs)
            log_time_value(timestamp_type, TimestampPeriod.END, *log_args, **log_kwargs)
            return result
        return wrapper
    return _create_timestamp_metric


class TimestampType:

    BEHAVIOR = "behavior"
    TRANSITION = "transition"

    class TimestampEvent:
        TYPE = "event"

        UPTIME = f"{TYPE}_uptime"
        LOADING_STATE = f"{TYPE}_loading_state"
        SAVING_STATE = f"{TYPE}_saving_state"
        DEPLOY = f"{TYPE}_deploy"
        UPDATE = f"{TYPE}_update"
        UPTIME_WAIT_ALL = f"{TYPE}_uptime_wait_all"
        SLEEPING = f"{TYPE}_sleeping"

    class TimestampInstruction:
        TYPE = "instruction"

        ADD = f"{TYPE}_add"
        DEL = f"{TYPE}_del"
        CONN = f"{TYPE}_conn"
        DCONN = f"{TYPE}_dcon"
        PUSH_B = f"{TYPE}_push_b"
        WAIT = f"{TYPE}_wait"
        WAITALL = f"{TYPE}_waitall"


class TimestampPeriod:
    START = "start"
    END = "end"


def init_time_log_dir(assembly_name: str, timestamp_expe_start: float):
    global ASSEMBLY_NAME
    global TIMESTAMP_EXPE_START
    ASSEMBLY_NAME = assembly_name
    TIMESTAMP_EXPE_START = timestamp_expe_start


def _compute_relative_time():
    return time.time() - TIMESTAMP_EXPE_START


def log_time_value(timestamp_type: str, timestamp_period: str, *args, **kwargs):
    register_time_value(timestamp_type, timestamp_period, *args, **kwargs)


def register_time_value(timestamp_type: str, timestamp_period: str, *args, component_timestamps_dict=None, **kwargs):
    parameters_args = "-".join(args)
    parameters_kwargs = "-".join(map(str, kwargs.values()))
    timestamp_name = timestamp_type
    if parameters_args != "":
        timestamp_name += f"_{parameters_args}"
    if parameters_kwargs != "":
        timestamp_name += f"_{parameters_kwargs}"

    if component_timestamps_dict is not None:
        timestamp_dict_to_save = component_timestamps_dict
    else:
        timestamp_dict_to_save = all_timestamps_dict
    if timestamp_period == TimestampPeriod.START:
        if timestamp_name in timestamp_dict_to_save.keys():

            # Il est possible qu'un behavior soit queued au même moment où le noeud se réveille, auquel cas on aurait une
            # redondance sur le start du timestamp du behavior. Cela est dûe au fait que la fonction semantics() du component
            # ne s'arrête pas si le noeud distant n'est pas dispo, car on n'a besoin d'intéragir avec le noeud distant uniquement
            # s'il y a une transition à faire TODO: fix la redondance
            if not global_variables.is_concerto_d_central():
                raise Exception(f"Register time value start error: {timestamp_name} for {TimestampPeriod.START} already registered")
            else:
                log_once.debug(f"Register time value start not done: {timestamp_name} for {TimestampPeriod.START} already registered")
        else:
            timestamp_dict_to_save[timestamp_name] = {}
            timestamp_dict_to_save[timestamp_name][TimestampPeriod.START] = _compute_relative_time()
            log.debug(f"Saved timestamp: {timestamp_type} {args} {kwargs} {timestamp_period}")

    else:
        if timestamp_name not in timestamp_dict_to_save.keys():

            # Cas concerto-d-central: Il est possible que le timestamp d'un behavior ait déjà été flush si le timestamp_state a été switch à sleeping,
            # qui provoque le END de tous les timestamps notamment de celui du behavior. La fonction standard appelée pour switch
            # le behavior provoque donc une redondance TODO: à simplifier dans le code
            if not global_variables.is_concerto_d_central():
                raise Exception(f"Register time value end error: {timestamp_name} never registered")
            else:
                log_once.debug(f"Register time value end not done: {timestamp_name} never registered")
        elif TimestampPeriod.END in timestamp_dict_to_save[timestamp_name]:
            raise Exception(f"Register time value end error: {timestamp_name} for {TimestampPeriod.END} already registered")
        else:
            timestamp_dict_to_save[timestamp_name][TimestampPeriod.END] = _compute_relative_time()
            log.debug(f"Saved timestamp: {timestamp_type} {args} {kwargs} {timestamp_period}")

    return timestamp_name


# TODO rename functions
def register_timestamps_in_file(component_timestamps_dict=None, component_name=None):
    time_in_ms = time.time() % 1000
    timestamp = datetime.now().strftime(f"%Y-%m-%d_%H-%M-%S-{time_in_ms}")
    if component_timestamps_dict is not None and component_name is not None:
        timestamp_dict_to_save = component_timestamps_dict
        name_to_save = component_name
    else:
        timestamp_dict_to_save = all_timestamps_dict
        name_to_save = ASSEMBLY_NAME

    log.debug(f"DUMPING FILE: {global_variables.execution_expe_dir}/{name_to_save}_{timestamp}.yaml")
    reconfiguration_dir = f"{global_variables.execution_expe_dir}/{global_variables.reconfiguration_name}"
    os.makedirs(f"{reconfiguration_dir}", exist_ok=True)
    with open(f"{reconfiguration_dir}/{name_to_save}_{timestamp}.yaml", "w") as f:
        yaml.safe_dump(timestamp_dict_to_save, f)


def register_end_all_time_values(component_timestamps_dict=None):
    if component_timestamps_dict is not None:
        timestamp_dict_to_save = component_timestamps_dict
    else:
        timestamp_dict_to_save = all_timestamps_dict

    for timestamp_name, timestamp_values in timestamp_dict_to_save.items():
        if TimestampPeriod.END not in timestamp_values.keys():
            log.debug(f"Saved timestamp: {timestamp_name} {TimestampPeriod.END}")
            timestamp_dict_to_save[timestamp_name][TimestampPeriod.END] = _compute_relative_time()
