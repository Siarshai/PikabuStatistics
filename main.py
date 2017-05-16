import pickle

from analytics_density_by_rating import analyze_rating_density
from analytics_density_by_tags_and_time import analyze_density_by_tag_and_time
from analytics_density_by_time import analyze_density_by_time
from analytics_rating_by_tag import analyze_tag_wise_mean_rating
from analytics_tags_correlation import analyze_tags_correlation


if __name__ == "__main__":
    with open("data.pkl", "rb") as handle:
        data = pickle.load(handle)

    analyze_density_by_time(data)
    analyze_rating_density(data)
    analyze_tag_wise_mean_rating(data)
    analyze_density_by_tag_and_time(data, begin_time=1388534401, end_time=1494115201)
    analyze_tags_correlation(data)


