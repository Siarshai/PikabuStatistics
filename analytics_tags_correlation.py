import os
import numpy as np
from performance.caching import save_code_based_cache
from drawing import draw_heat_square_matrix
from utils import clean_folders, filter_tags_by_occurency_number

RESULT_FOLDER = "tags_correlation"

@save_code_based_cache("tags_distance.pkl")
def _compute_tags_distance(data, tags, method, **kwargs):
    l = len(tags)
    distance_mat = np.zeros(shape=(l, l))

    if method == "chisquare":
        for idx1, tag1 in enumerate(tags):
            print("Computing distance {}/{}".format(idx1 + 1, len(tags)))
            for idx2, tag2 in enumerate(tags[idx1+1:]):
                a, b, c, d = 0, 0, 0, 0
                for post in data.values():
                    tag1in, tag2in = tag1 in post["tags"], tag2 in post["tags"]
                    if not tag1in and not tag2in:
                        a += 1
                    elif not tag1in and tag2in:
                        b += 1
                    elif tag1in and not tag2in:
                        c += 1
                    else:
                        d += 1
                chi = (a + b + c + d)*(a*d - b*c)*(a*d - b*c)/((a + b)*(a + c)*(b + d)*(c + d))
                distance_mat[idx1, idx2 + idx1 + 1] = chi
                distance_mat[idx2 + idx1 + 1, idx1] = chi
    else:
        for post in data.values():
            for i, tag1 in enumerate(post["tags"]):
                if tag1 in tags:
                    idx1 = tags.index(tag1)
                    distance_mat[idx1, idx1] -= 1
                    for tag2 in post["tags"][i+1:]:
                        if tag2 in tags:
                            idx2 = tags.index(tag2)
                            distance_mat[idx1, idx2] -= 1
                            distance_mat[idx2, idx1] -= 1

    return distance_mat, tags


def _analyze_tags_correlation_subtask(data, tags, filename, figsize, save_code):
    fullname = os.path.join(RESULT_FOLDER, filename)
    distance_mat, filtered_sorted_tags = _compute_tags_distance(data, tags, method="chisquare", save_code=save_code)
    distance_mat = np.sqrt(distance_mat)
    draw_heat_square_matrix(distance_mat, filtered_sorted_tags, path_to_save=fullname, figsize=figsize)


def analyze_tags_correlation(data, tags=None):
    print("Analyzing tags correlation")
    clean_folders([RESULT_FOLDER])
    if tags is None:
        tags = filter_tags_by_occurency_number(data, tag_occurencies_filter=lambda v: v >= 3500, save_code=612)
        _analyze_tags_correlation_subtask(data, tags, "tags_correlation_heatmat.png", figsize=(14, 14), save_code=612)
        tags = filter_tags_by_occurency_number(data, tag_occurencies_filter=lambda v: v >= 5000, save_code=111)
        _analyze_tags_correlation_subtask(data, tags, "lores_tags_correlation_heatmat.png", figsize=(9, 9), save_code=111)
    else:
        _analyze_tags_correlation_subtask(data, tags, "tags_correlation_heatmat.png",(14, 14), save_code=0)
