import math


class RankingService:
    WEIGHT_VIEWS = 0.4
    WEIGHT_LIKES = 0.35
    WEIGHT_COMMENTS = 0.25

    def compute_rank_score(self, views: int, likes: int, comments: int) -> float:
        return (
            math.log1p(views) * self.WEIGHT_VIEWS
            + math.log1p(likes) * self.WEIGHT_LIKES
            + math.log1p(comments) * self.WEIGHT_COMMENTS
        )

    def compute_engagement_rate(self, views: int, likes: int, comments: int, shares: int = 0) -> float:
        return (likes + comments + shares) / max(views, 1)
