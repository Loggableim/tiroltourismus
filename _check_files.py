import json, os
data_dir = "F:/tiroltourismus/src/data/unterkuenfte"
for bn in range(201, 206):
    bf = "F:/tiroltourismus/scripts/batches/batch_%d.json" % bn
    for item in json.load(open(bf, encoding="utf-8")):
        slug = item["slug"]
        fp = os.path.join(data_dir, slug, "index.json")
        if not os.path.exists(fp):
            print("Batch %d: %s (%s) -> fehlt!" % (bn, item["name"], slug))
