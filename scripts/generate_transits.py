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


# global cache for Horizons
JPL_CACHE = {}


def batch_fetch_horizons(start, stop):

    results = {}

    for body in BODIES:

        try:

            rows = fetch_batch(body,start,stop)

            results[body] = rows

        except Exception:

            results[body] = None

    return results


def missing(rows):

    return [i for i,r in enumerate(rows) if r["lon"] is None]


def resolve_body(body,start_date):

    start=start_date.strftime("%Y-%m-%d")
    stop=(start_date+timedelta(days=6)).strftime("%Y-%m-%d")

    results=[{"lon":None,"lat":None,"source":"none"} for _ in range(7)]

    # 1 JPL cached
    if body in JPL_CACHE and JPL_CACHE[body]:

        for i,(lon,lat) in enumerate(JPL_CACHE[body][:7]):

            if lon is not None:

                results[i]={"lon":lon,"lat":lat,"source":"JPL"}

    # 2 Miriade
    m=missing(results)

    if m:

        try:

            rows=fetch_miriade(body,start,stop)

            for i,row in enumerate(rows):

                if i in m and row["lon"] is not None:

                    results[i]={"lon":row["lon"],"lat":row["lat"],"source":"Miriade"}

        except Exception as e:

            print(f"[WARN] Miriade failed {body}: {e}")

    # 3 MPC propagation
    m=missing(results)

    if m:

        try:

            rows=fetch_mpc(body,start,stop)

            for i,row in enumerate(rows):

                if i in m and row["lon"] is not None:

                    results[i]={"lon":row["lon"],"lat":row["lat"],"source":"MPC"}

        except Exception as e:

            print(f"[WARN] MPC failed {body}: {e}")

    # 4 Swiss fallback
    m=missing(results)

    if m:

        try:

            rows=fetch_swiss(body,start,stop)

            for i,row in enumerate(rows):

                if i in m and row["lon"] is not None:

                    results[i]={"lon":row["lon"],"lat":row["lat"],"source":"Swiss"}

        except Exception as e:

            print(f"[WARN] Swiss failed {body}: {e}")

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

    out=[]

    for i in range(7):

        try:

            sun=data["Sun"][i]["lon"]

            if sun is None:

                out.append({})

                continue

            h=compute_harmonics([sun])

            out.append({
                "sun_h5":float(h["h5"][0]),
                "sun_h7":float(h["h7"][0]),
                "sun_h9":float(h["h9"][0])
            })

        except:

            out.append({})

    return out


def compute_star_conjunctions(data):

    stars=get_fixed_star_catalog()

    hits=[]

    for day in range(7):

        events=[]

        for body in data:

            lon=data[body][day]["lon"]

            if lon is None:

                continue

            for star,slon in stars.items():

                diff=abs((lon-slon+180)%360-180)

                if diff<1:

                    events.append({
                        "body":body,
                        "star":star,
                        "orb":round(diff,3)
                    })

        hits.append(events)

    return hits


def main():

    start_date=datetime.utcnow()

    start=start_date.strftime("%Y-%m-%d")
    stop=(start_date+timedelta(days=6)).strftime("%Y-%m-%d")

    global JPL_CACHE

    print("Fetching JPL batch")

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

                print(f"[ERROR] {body} failed: {e}")

                bodies[body]=[]

    data={

        "generated":datetime.utcnow().isoformat(),

        "bodies":bodies

    }

    data["arabic_parts"]=calc_arabic_parts(bodies)

    data["harmonics"]=calc_harmonics(bodies)

    data["fixed_star_conjunctions"]=compute_star_conjunctions(bodies)

    with open("docs/current_week.json","w") as f:

        json.dump(data,f,indent=2)

    print("current_week.json written")


if __name__=="__main__":

    main()
