# common/version.py
def parse_version(version_str):
    """
    Parses version string like v1.32000 → (x, y, z, i, q)
    x = ranking type (1=Boolean, 2=TF, 3=TF-IDF)
    y = datastore type (1=JSON, 2=SQLite)
    z = compression type
    i = index optimization flag
    q = query processing flag
    """
    # remove 'v1.' prefix and split digits
    core = version_str.replace("v1.", "")
    if len(core) < 5:
        core = core.ljust(5, "0")  # pad with zeros if short

    x = int(core[0])
    y = int(core[1])
    z = int(core[2])
    i = int(core[3])
    q = int(core[4])
    return x, y, z, i, q
