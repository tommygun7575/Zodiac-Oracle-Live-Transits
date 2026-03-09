import requests

HORIZONS_URL = "https://ssd.jpl.nasa.gov/horizons_batch.cgi"

def fetch_ephemeris(body_id, start_date, stop_date, step_size="2d"):

    center = "500@0" if body_id == "10" else "500@399"

    batch_payload = f"""
COMMAND='{body_id}'
CENTER='{center}'
MAKE_EPHEM='YES'
EPHEM_TYPE='OBSERVER'
START_TIME='{start_date}'
STOP_TIME='{stop_date}'
STEP_SIZE='{step_size}'
QUANTITIES='1'
CSV_FORMAT='YES'
"""

    response = requests.post(
        HORIZONS_URL,
        data={
            "batch": batch_payload,
            "format": "text"
        },
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError(f"Horizons HTTP error {response.status_code}")

    text = response.text

    if "$$SOE" not in text:
        raise RuntimeError("Horizons did not generate ephemeris table")

    lines = text.splitlines()

    ephemeris = []
    capture = False

    for line in lines:

        if "$$SOE" in line:
            capture = True
            continue

        if "$$EOE" in line:
            break

        if capture:
            parts = line.split(",")

            if len(parts) >= 2:
                try:
                    date = parts[0].strip()
                    lon = float(parts[1].strip())
                    ephemeris.append({
                        "date": date,
                        "longitude_deg": lon
                    })
                except:
                    continue

    if not ephemeris:
        raise RuntimeError("Parsed zero ephemeris rows")

    return ephemeris
