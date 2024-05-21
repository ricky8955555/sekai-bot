def parse_bool(string: str) -> bool:
    if string in ["t", "true", "T", "True", "TRUE", "1", "yes", "Yes", "YES", "y", "Y"]:
        return True
    if string in ["f", "false", "F", "False", "FALSE", "0", "no", "No", "NO", "n", "N"]:
        return False
    raise ValueError
