import warnings
import numpy as np
from drawing import draw_rating_violinplot
from utils import timestamp_to_date, clean_folders
import os


# http://pikabu.ru/story/styid_3022955
# http://pikabu.ru/story/to_nelovkoe_chuvstvo_kogda_vse_govoryat_pro_kakogoto_kotika_3219427
# 0x00 http://pikabu.ru/story/pravosudie_potekhasski_2478847
# http://pikabu.ru/story/true_story_3001448
# http://pikabu.ru/story/novogodnee_pozdravlenie_4722555
# http://pikabu.ru/story/vospityivaem_shkolnika_v_internete_2275942
# http://pikabu.ru/story/vyigonim_skorpiona_s_shapki_sayta_3262947
# http://pikabu.ru/story/moderator_vs_zombies_2177316


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

    hlines.append([1.0, p999, "99.9 перцентиль ({0:.2f})".format(p999)])
    hlines.append([1.0, p99, "99 перцентиль ({0:.2f})".format(p99)])
    hlines.append([1.0, p95, "95 перцентиль ({0:.2f})".format(p95)])
    hlines.append([0.61, 0.0, "Индекс Джини: {0:.4f}".format(gini)])
    scatter_top_posts = list(zip([1.0]*80, ratings[:80]))
    name = os.path.join(RESULT_FOLDER, "rating_violinplot.png")
    draw_rating_violinplot(ratings, hlines=hlines, scatter=scatter_top_posts, path_to_save=name)
    name = os.path.join(RESULT_FOLDER, "lores_rating_violinplot.png")
    hlines = [hlines[0]] + [hlines[2]] + [hlines[4]] + [hlines[6]] + hlines[-4:]
    draw_rating_violinplot(ratings, hlines=hlines,
                           scatter=scatter_top_posts[:25], path_to_save=name, figsize=(8, 10))