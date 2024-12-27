_ERROR_MAP = {
    "SUCCEEDED": 200,
    "DB CONNECTION FAILED": 301,
    "CRUD FAILED": 302,
    "INVALID MATCHED DATA": 302,
    "FAILED ATTACH BASE URL": 401,
    "UNWRAP FAILED": 501,
    "WEB CONNECTION FAILED": 502,
    "DOWNLOAD FAILED": 503,
    "UPLOAD FAILED": 504,
    "NOT FOUND CORRECT FORM": 601,
    "NOT FOUND URL IN DB": 602,
    "FAILED FORMATTING": 603,
}

def get_error_code(message: str):
    caps = message.upper()
    if caps not in _ERROR_MAP:
        return -1
    else:
        return _ERROR_MAP[caps]
    