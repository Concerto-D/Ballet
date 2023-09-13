def add_mzn_ext(x: str) -> str:
    if x[-4:] != ".mzn":
        return x + ".mzn"
    else:
        return x


mzn_max_int = 1000000
