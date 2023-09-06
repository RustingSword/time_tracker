import json
import re
import urllib.parse

import matplotlib.pyplot as plt
import pandas as pd


def parse_title(row):
    if pd.isnull(row["title"]):
        return "Unknown"
    if "Google Chrome" in row["app_name"]:
        url_match = re.search(r"https?://[^\s]*", row["title"])
        if url_match:
            return urllib.parse.urlparse(url_match.group()).netloc
        else:
            return "Unknown URL"
    else:
        return row["app_name"]


def map_activity_to_category(activity, app_categories):
    if activity in app_categories:
        return app_categories[activity]

    category = input(f"Enter the category for activity '{activity}': ")
    app_categories[activity] = category

    return category


def process_data():
    activity_df = pd.read_csv("activity_log.csv")

    with open("app_categories.json", "r") as f:
        app_categories = json.load(f)

    activity_df["duration"] = (
        activity_df["timestamp"].shift(-1) - activity_df["timestamp"]
    )

    activity_df = activity_df[:-1]

    activity_df["activity"] = activity_df.apply(parse_title, axis=1)

    activity_df["mapped_category"] = activity_df["activity"].apply(
        lambda x: map_activity_to_category(x, app_categories)
    )
    activity_df = activity_df[activity_df["mapped_category"] != "unknown"]

    with open("app_categories.json", "w") as f:
        json.dump(app_categories, f, indent=4, ensure_ascii=False)

    category_accumulated_time_seconds_mapped = (
        activity_df.groupby("mapped_category")["duration"]
        .sum()
        .sort_values(ascending=False)
    )

    category_accumulated_time_minutes_mapped = (
        category_accumulated_time_seconds_mapped / 60
    )
    return category_accumulated_time_minutes_mapped


def plot_data(data):
    plt.figure(figsize=(10, 6))
    data.sort_values().plot(kind="barh")
    print(data.to_markdown())
    plt.title("Accumulated Usage of Each Activity Category")
    plt.xlabel("Accumulated Time (minutes)")
    plt.ylabel("Activity Category")
    plt.grid(axis="x")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    data = process_data()
    plot_data(data)
