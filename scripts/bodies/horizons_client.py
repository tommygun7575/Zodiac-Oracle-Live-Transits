def parse_ephemeris(text):

    reading = False
    header = None
    lon_index = None

    rows = []

    for line in text.splitlines():

        if "$$SOE" in line:
            reading = True
            continue

        if "$$EOE" in line:
            break

        if not reading:

            if "Date__(UT)__HR:MN" in line or "Date__(UT)__HR:MN:SC" in line:
                header = [h.strip() for h in line.split(",")]

                for i, col in enumerate(header):
                    if "EclLon" in col or "Lon" in col:
                        lon_index = i

        else:

            parts = line.split(",")

            if lon_index is not None and len(parts) > lon_index:

                try:

                    rows.append({
                        "date": parts[0].strip(),
                        "lon": float(parts[lon_index])
                    })

                except:
                    pass

    return rows
