def store(bank, key, data, cachedir):
    return True


def fetch(bank, key, cachedir):
    return {"bank": bank, "key": key}
