import warnings
import numpy as np
from drawing import draw_rating_violinplot, draw_rating_plot, draw_post_number_logplot
from utils import timestamp_to_date, clean_folders, discretize
import os


RESULT_FOLDER = "rating_density"


def _compute_gini_coefficient(X, nquants=250):
    X = np.asarray(sorted(X))
    csX = np.cumsum(X)
    csX = csX / float(csX[-1])
    n = len(X)
    q = n//nquants

    cumarea = 0
    for i in range(1, nquants):
        cumarea += csX[i*q] + csX[(i-1)*q]

    gini = 1 - (1.0/nquants)*cumarea
    return gini


def analyze_rating_density(data):

    print("Analyze rating overall density")
    clean_folders([RESULT_FOLDER])

    ratings = sorted([v["rating"] for v in data.values()], reverse=True)
    names = []
    hlines = []
    idxes = list(range(8)) + [11, 15, 20, 30, 40, 60, 80]
    for i in idxes:
        r = ratings[i]
        try:
            record = next(record for record in data.values() if record["rating"] == r)
            hlines.append([0.61 + 0.285*(i%2), r, record["title"] + " (р:" + str(r) + ", " + timestamp_to_date(record["timestamp"]) + ")"])
            names.append(record["title"])
        except StopIteration as si:
            warnings.warn("Could not find record with such rating: {}".format(r), RuntimeWarning)

    gini = _compute_gini_coefficient(ratings)
    p999 = np.percentile(ratings, 99.9)
    p99 = np.percentile(ratings, 99)
    p95 = np.percentile(ratings, 95)
    mean = np.mean(ratings)
    median = np.median(ratings)

    hlines.append([1.0, p999, "99.9 перцентиль ({0:.2f})".format(p999)])
    hlines.append([1.0, p99, "99 перцентиль ({0:.2f})".format(p99)])
    hlines.append([1.0, p95, "95 перцентиль ({0:.2f})".format(p95)])
    hlines.append([0.61, 0.0, "Индекс Джини: {0:.4f}, среднее: {1:.2f}, медиана: {2:.2f}".format(gini, mean, median)])
    scatter_top_posts = list(zip([1.0]*80, ratings[:80]))
    name = os.path.join(RESULT_FOLDER, "rating_violinplot.png")
    draw_rating_violinplot(ratings, hlines=hlines, scatter=scatter_top_posts, path_to_save=name)
    name = os.path.join(RESULT_FOLDER, "lores_rating_violinplot.png")
    hlines = [hlines[0]] + [hlines[2]] + [hlines[4]] + [hlines[6]] + hlines[-4:]
    draw_rating_violinplot(ratings, hlines=hlines,
                           scatter=scatter_top_posts[:25], path_to_save=name, figsize=(8, 10))

    n_bins_for_logplot = 100
    N = discretize([r for r in ratings if 100 < r <= 10000], bins=n_bins_for_logplot, normalize=False)
    name = os.path.join(RESULT_FOLDER, "logplot.png")
    draw_post_number_logplot([n_bins_for_logplot*i for i in range(len(N))],
                             [N],
                             [u"Количество постов"],
                             path_to_save=name)
    name = os.path.join(RESULT_FOLDER, "loores_logplot.png")
    draw_post_number_logplot([n_bins_for_logplot*i for i in range(len(N))],
                             [N],
                             [u"Количество постов"],
                             path_to_save=name,
                             figsize=(14, 8))

