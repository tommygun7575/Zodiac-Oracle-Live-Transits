import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from scripts.bodies.horizons_engine import fetch_batch
from scripts.bodies.miriade_engine import fetch_miriade
from scripts.bodies.swiss_engine import fetch_swiss
from scripts.bodies.mpc_client import fetch_mpc
from scripts.bodies.harmonics_engine import compute_harmonics
from scripts.fixed_stars import get_fixed_star_catalog


BODIES = [
    "Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
    "Uranus","Neptune","Pluto",
    "Ceres","Pallas","Juno","Vesta",
    "Eris","Sedna","Orcus","Makemake","Haumea","Quaoar","Ixion"
]


JPL_CACHE = {}


def batch_fetch_horizons(start, stop):

    cache = {}

    for body in BODIES:

        try:

            rows = fetch_batch(body, start, stop)

            cache[body] = rows

        except Exception:

            cache[body] = None

    return cache


def missing_indices(rows):

    return [i for i,r in enumerate(rows) if r["lon"] is None]


def resolve_body(body, start_date):

    start = start_date.strftime("%Y-%m-%d")
    stop = (start_date + timedelta(days=6)).strftime("%Y-%m-%d")

    results = [{"lon":None,"lat":None,"source":"none"} for _ in range(7)]

    if body in JPL_CACHE and JPL_CACHE[body]:

        for i,(lon,lat) in enumerate(JPL_CACHE[body][:7]):

            if lon is not None:
                results[i] = {"lon":lon,"lat":lat,"source":"JPL"}

    missing = missing_indices(results)

    if missing:

        try:

            rows = fetch_miriade(body,start,stop)

            for i,row in enumerate(rows):

                if i in missing and row["lon"] is not None:

                    results[i] = {
                        "lon":row["lon"],
                        "lat":row["lat"],
                        "source":"Miriade"
                    }

        except Exception as e:

            print(f"[WARN] Miriade failed for {body}: {e}")

    missing = missing_indices(results)

    if missing:

        try:

            rows = fetch_mpc(body,start,stop)

            for i,row in enumerate(rows):

                if i in missing and row["lon"] is not None:

                    results[i] = {
                        "lon":row["lon"],
                        "lat":row["lat"],
                        "source":"MPC"
                    }

        except Exception as e:

            print(f"[WARN] MPC propagation failed for {body}: {e}")

    missing = missing_indices(results)

    if missing:

        try:

            rows = fetch_swiss(body,start,stop)

            for i,row in enumerate(rows):

                if i in missing and row["lon"] is not None:

                    results[i] = {
                        "lon":row["lon"],
                        "lat":row["lat"],
                        "source":"Swiss"
                    }

        except Exception as e:

            print(f"[WARN] Swiss fallback failed for {body}: {e}")

    return results


def calc_arabic_parts(data):

    parts=[]

    for i in range(7):

        try:

            sun=data["Sun"][i]["lon"]
            moon=data["Moon"][i]["lon"]

            if sun is None or moon is None:

                parts.append({"part_of_fortune":None})

            else:

                parts.append({"part_of_fortune":(moon-sun)%360})

        except:

            parts.append({"part_of_fortune":None})

    return parts


def calc_harmonics(data):

    results=[]

    for i in range(7):

        try:

            sun=data["Sun"][i]["lon"]

            if sun is None:
                results.append({})
                continue

            h=compute_harmonics([sun])

            results.append({
                "sun_h5":float(h["h5"][0]),
                "sun_h7":float(h["h7"][0]),
                "sun_h9":float(h["h9"][0])
            })

        except:
            results.append({})

    return results


def compute_fixed_star_conjunctions(data):

    stars=get_fixed_star_catalog()

    results=[]

    for i in range(7):

        hits=[]

        for body in data:

            lon=data[body][i]["lon"]

            if lon is None:
                continue

            for star,star_lon in stars.items():

                diff=abs((lon-star_lon+180)%360-180)

                if diff<1:

                    hits.append({
                        "body":body,
                        "star":star,
                        "orb":round(diff,3)
                    })

        results.append(hits)

    return results


def main():

    start_date=datetime.utcnow()

    start=start_date.strftime("%Y-%m-%d")
    stop=(start_date+timedelta(days=6)).strftime("%Y-%m-%d")

    global JPL_CACHE

    print("Fetching JPL ephemeris batch")

    JPL_CACHE=batch_fetch_horizons(start,stop)

    bodies={}

    with ThreadPoolExecutor(max_workers=6) as executor:

        futures={}

        for body in BODIES:

            futures[executor.submit(resolve_body,body,start_date)]=body

        for future in as_completed(futures):

            body=futures[future]

            try:
                bodies[body]=future.result()

            except Exception as e:

                print(f"[ERROR] Failed resolving {body}: {e}")

                bodies[body]=[]

    data={
        "generated":datetime.utcnow().isoformat(),
        "bodies":bodies
    }

    data["arabic_parts"]=calc_arabic_parts(bodies)

    data["harmonics"]=calc_harmonics(bodies)

    data["fixed_star_conjunctions"]=compute_fixed_star_conjunctions(bodies)

    with open("docs/current_week.json","w") as f:
        json.dump(data,f,indent=2)

    print("current_week.json written")


if __name__=="__main__":
    main()
