"""Vendor performance segmentation and scoring.

Clusters vendors with KMeans on aggregate revenue, order volume, and
reliability (1 - failed-order rate) so the admin dashboard can group
vendors into tiers (e.g. high-growth / steady / at-risk) instead of
someone eyeballing a spreadsheet, and produces a single weighted
composite score for ranking within/across tiers.

KMeans (rather than a supervised model) is used because there is no
ground-truth "vendor quality" label to train against — this is
exploratory segmentation, not prediction. Cluster IDs are arbitrary
(0/1/2, not ordered by "goodness"); the composite_score is what should
be used for ranking, and cluster is for grouping similar vendors.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from app.ml.features import build_vendor_week_features

# Relative importance of each signal in the composite score. Revenue is
# weighted highest since it's the primary business outcome; reliability
# still matters but a vendor with occasional failed orders and otherwise
# strong volume shouldn't be penalized as heavily as low revenue is.
SCORE_WEIGHTS = {"total_revenue": 0.5, "total_orders": 0.3, "reliability": 0.2}


def score_vendors(n_clusters: int = 3) -> pd.DataFrame:
    df = build_vendor_week_features()
    if df.empty:
        return df

    vendor_summary = (
        df.groupby("vendor_id")
        .agg(
            total_revenue=("revenue_inr", "sum"),
            total_orders=("orders", "sum"),
            total_failed=("failed_orders", "sum"),
        )
        .reset_index()
    )
    vendor_summary["reliability"] = (
        1 - (vendor_summary["total_failed"] / vendor_summary["total_orders"].replace(0, np.nan))
    ).fillna(0)

    feature_cols = ["total_revenue", "total_orders", "reliability"]
    features = vendor_summary[feature_cols]

    effective_clusters = max(1, min(n_clusters, len(vendor_summary)))
    if effective_clusters > 1:
        scaled = StandardScaler().fit_transform(features)
        kmeans = KMeans(n_clusters=effective_clusters, random_state=42, n_init=10)
        vendor_summary["cluster"] = kmeans.fit_predict(scaled)
    else:
        vendor_summary["cluster"] = 0

    # Min-max normalize revenue/orders onto reliability's natural 0-1
    # scale before combining, so one raw-magnitude signal (revenue in
    # rupees) doesn't dominate the weighted sum by construction.
    span = (features.max() - features.min()).replace(0, 1)
    norm = (features - features.min()) / span
    vendor_summary["composite_score"] = (
        norm["total_revenue"] * SCORE_WEIGHTS["total_revenue"]
        + norm["total_orders"] * SCORE_WEIGHTS["total_orders"]
        + vendor_summary["reliability"] * SCORE_WEIGHTS["reliability"]
    ).round(4)

    return vendor_summary.sort_values("composite_score", ascending=False).reset_index(drop=True)
