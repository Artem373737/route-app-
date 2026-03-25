from flask import Flask, render_template, request
import pandas as pd
import openrouteservice
import re
import os

app = Flask(__name__)

client = openrouteservice.Client(
    key=os.environ.get("ORS_KEY")
)

START = "Кривий Ріг, бульв. Вечірній, 35"

def clean(addr):
    addr = str(addr)
    addr = re.sub(r"\+\d+", "", addr)
    addr = re.sub(r"кв\.\s*\d+", "", addr, flags=re.I)
    if "Кривий Ріг" not in addr:
        addr += ", Кривий Ріг"
    return addr.strip()

def geocode(a):
    r = client.pelias_search(text=a)
    return r["features"][0]["geometry"]["coordinates"]

def optimize(addresses):
    coords = [geocode(a) for a in addresses]

    jobs = [{"id": i, "location": c} for i, c in enumerate(coords)]

    route = client.optimization(
        jobs=jobs,
        vehicles=[{
            "id": 1,
            "start": geocode(START),
            "end": geocode(START)
        }]
    )

    order = [s["job"] for s in route["routes"][0]["steps"] if "job" in s]
    return [addresses[i] for i in order]

def chunks(lst, n=10):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def build_link(points):
    return "https://www.google.com/maps/dir/" + "/".join(points)

@app.route("/", methods=["GET","POST"])
def index():
    routes = []

    if request.method == "POST":
        f = request.files["file"]
        df = pd.read_csv(f)

        raw = df.iloc[:,1].tolist()
        cleaned = [clean(a) for a in raw]

        opt = optimize(cleaned)

        for c in chunks(opt, 8):
            route = [START] + c + [START]
            routes.append(build_link(route))

    return render_template("index.html", routes=routes)

if __name__ == "__main__":
    app.run()
