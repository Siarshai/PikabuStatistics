import os
import numpy as np
from performance.caching import simple_cache
from drawing import draw_rating_bar_chart
from utils import clean_folders, filter_tags_by_occurency_number

RESULT_FOLDER = "tag_wise_mean_rating"

def analyze_tag_wise_mean_rating(data, tags=None):
    print("Analyzing tag wise mean rating")

    clean_folders([RESULT_FOLDER])
    if tags is None:
        tags = filter_tags_by_occurency_number(data, tag_occurencies_filter=lambda v: v >= 200, save_code=413)

    mean_tag_wise_rating = compute_tag_wise_mean_rating(data, tags)
    path_to_save = os.path.join(RESULT_FOLDER, "tag_wise_mean_rating_barchart.png")
    draw_rating_bar_chart(mean_tag_wise_rating, path_to_save=path_to_save)
    path_to_save = os.path.join(RESULT_FOLDER, "lores_tag_wise_mean_rating_barchart.png")
    draw_rating_bar_chart(mean_tag_wise_rating, path_to_save=path_to_save, bars_threshold=24, figsize=(12, 9))


@simple_cache("tag_wise_mean_rating.pkl")
def compute_tag_wise_mean_rating(data, tags):
    print("Computing mean tag wise rating")
    result = {}
    number_of_tags = len(tags)
    for i, tag in enumerate(tags):
        if not (i + 1)%50:
            print("{}/{}".format(i + 1, number_of_tags))
        result[tag] = np.mean([d["rating"] for d in data.values() if tag in d["tags"]])
    return result