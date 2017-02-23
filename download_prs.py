#!/usr/bin/env python3
import os
import pandas
import requests

df = pandas.read_csv("ukfpseudoblog_entry_export.csv")
df.columns = ["id", "url"]


def download_to_file(row):
    try:
        if not os.path.exists(os.path.join("html", "pseudoblog_{}.html".format(row.id))):
            r = requests.get(row.url)
            print("Got {}.".format(row.url))
            with open("html/pseudoblog_{}.html".format(row.id), "w") as f:
                f.write(r.text)
    except requests.exceptions.ConnectionError:
        pass

df.apply(download_to_file, axis=1)
