import re

def addYamlExtension(name: str) -> str:
    return name + ".yaml" if not name.endswith(".yaml") else name

def replace_variables(string, variables):
    # Find all occurrences of "${{ v }}" in the string
    for match in re.finditer(r'\$\{\{\s*(\w+)\s*\}\}', string):
        variable_name = match.group(1)
        if variable_name in variables:
            string = string.replace("${{ "+ variable_name + " }}", str(variables[variable_name]))
    return string

def extract_loop_values(string, variables):
    match = re.match(r'\$\{\{ each (\w+) in range\((\d+),(\w+)\)\}\}', string)
    if match:
        variable, lower_bound, higher_bound = match.groups()
        try:
            lbound = int(lower_bound)
        except ValueError:
            lbound = variables[lower_bound]
        try:
            hbound = int(higher_bound)
        except ValueError:
            hbound = variables[higher_bound]
        return variable, lbound, hbound
    raise ValueError(f"Can't extract variable name and its bound from: `{string}`")