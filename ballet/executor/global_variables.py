CONCERTO_D_SYNCHRONOUS = "synchronous"
CONCERTO_D_ASYNCHRONOUS = "asynchronous"
CONCERTO_D_CENTRAL = "central"
INVENTORY_FILE_PATH = "inventory.yaml"


execution_expe_dir = None
concerto_d_version = None
reconfiguration_name = ""

current_nb_instructions_done = 0


def is_concerto_d_asynchronous():
    return concerto_d_version == CONCERTO_D_ASYNCHRONOUS


def is_concerto_d_central():
    return concerto_d_version == CONCERTO_D_CENTRAL


def get_inventory_absolute_path():
    return f"{execution_expe_dir}/{INVENTORY_FILE_PATH}"
