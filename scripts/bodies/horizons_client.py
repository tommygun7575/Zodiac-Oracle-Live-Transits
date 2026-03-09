import requests

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

def fetch_ephemeris(body_id, start_date, stop_date, step_size="2d"):

    center = "500@0" if body_id == "10" else "500@399"

    params = {
        "format": "text",
        "COMMAND": body_id,
        "MAKE_EPHEM": "YES",
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": center,
        "START_TIME": start_date,
        "STOP_TIME": stop_date,
        "STEP_SIZE": step_size,
        "QUANTITIES": "1",
        "CSV_FORMAT": "YES"
    }

    response = requests.get(HORIZONS_URL, params=params, timeout=30)

    print("==== RAW RESPONSE BEGIN ====")
    print(response.text[:2000])
    print("==== RAW RESPONSE END ====")

    raise RuntimeError("Debug stop")
