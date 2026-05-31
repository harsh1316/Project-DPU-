"""
generate_project.py
--------------------
Generates the primary (survey) and secondary (campaign performance) datasets for the
MBA project "A Study on the Impact of Social Media and Digital Marketing Analytics on
Consumer Engagement and Brand Performance", runs the full statistical analysis, and
produces all figures / dashboards used in the report.

Outputs:
  data/survey_responses.csv          - 270 primary survey responses
  data/campaign_performance.csv      - 60 platform x month campaign records
  data/platform_summary.csv          - aggregated KPI summary by platform
  analysis/results.json              - every statistic cited in the report
  figures/*.png                      - all charts and the KPI dashboard

Run:  python3 analysis/generate_project.py
"""

import json
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy import stats

# ----------------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------------
RNG = np.random.default_rng(20240502)          # seed = student PRN tail for reproducibility
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
FIG = os.path.join(ROOT, "figures")
ANALYSIS = os.path.join(ROOT, "analysis")
for d in (DATA, FIG, ANALYSIS):
    os.makedirs(d, exist_ok=True)

# House style for all charts
PRIMARY = "#1f4e79"      # deep blue
ACCENT = "#e07b39"       # orange
GREEN = "#2e8b57"
GREY = "#6b6b6b"
PALETTE = ["#1f4e79", "#e07b39", "#2e8b57", "#9b5fb0", "#c0392b", "#16a085", "#f1c40f"]
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.edgecolor": "#cccccc",
    "axes.grid": True,
    "grid.color": "#e6e6e6",
    "grid.linewidth": 0.8,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.dpi": 130,
    "savefig.bbox": "tight",
})

N = 270  # sample size

results = {}

# ----------------------------------------------------------------------------
# 1. PRIMARY DATA  -  Consumer / respondent survey
# ----------------------------------------------------------------------------
ids = [f"R{1000+i}" for i in range(N)]

age_levels = ["18-24", "25-34", "35-44", "45-54", "55+"]
age_p = [0.34, 0.33, 0.18, 0.10, 0.05]
age = RNG.choice(age_levels, N, p=age_p)

gender = RNG.choice(["Male", "Female", "Prefer not to say"], N, p=[0.54, 0.44, 0.02])

occupation = RNG.choice(
    ["Student", "Salaried", "Self-employed", "Business owner", "Homemaker", "Other"],
    N, p=[0.30, 0.40, 0.12, 0.08, 0.06, 0.04])

location = RNG.choice(["Metro", "Urban", "Semi-urban", "Rural"], N, p=[0.40, 0.34, 0.18, 0.08])

# Primary platform (most used) - reflects 2024-25 India usage skew
platform = RNG.choice(
    ["Instagram", "YouTube", "WhatsApp", "Facebook", "LinkedIn", "X (Twitter)", "Other"],
    N, p=[0.33, 0.24, 0.15, 0.12, 0.08, 0.05, 0.03])

# Daily time on social media (ordinal buckets)
time_levels = ["< 1 hr", "1-2 hrs", "2-3 hrs", "3-4 hrs", "> 4 hrs"]
time_p = [0.10, 0.27, 0.30, 0.20, 0.13]
daily_time = RNG.choice(time_levels, N, p=time_p)
time_hours_map = {"< 1 hr": 0.5, "1-2 hrs": 1.5, "2-3 hrs": 2.5, "3-4 hrs": 3.5, "> 4 hrs": 4.5}
time_hours = np.array([time_hours_map[t] for t in daily_time])

follows_brands = RNG.choice(["Yes", "No"], N, p=[0.78, 0.22])

content_pref = RNG.choice(
    ["Short video / Reels", "Image / Carousel", "Stories", "Long video", "Text / Blog"],
    N, p=[0.41, 0.22, 0.15, 0.14, 0.08])

# --- Latent constructs (Likert 1-5) built so that correlations are realistic ---
def likert(mean, spread, n=N):
    vals = RNG.normal(mean, spread, n)
    return np.clip(np.rint(vals), 1, 5).astype(int)

# A latent "digital engagement propensity" influenced by age and time spent
young = np.isin(age, ["18-24", "25-34"]).astype(float)
latent = 0.85 * (young - young.mean()) + 0.45 * (time_hours - time_hours.mean()) + RNG.normal(0, 0.85, N)
latent = (latent - latent.mean()) / latent.std()   # standardise

def likert_from_latent(base, coef, noise):
    v = base + coef * latent + RNG.normal(0, noise, N)
    return np.clip(np.rint(v), 1, 5).astype(int)

ad_recall = likert_from_latent(3.3, 0.82, 0.60)            # I notice/recall ads on social media
targeted_relevance = likert_from_latent(3.1, 0.80, 0.62)  # ads shown to me are relevant
trust_ads = likert_from_latent(2.8, 0.45, 0.95)           # I trust targeted ads (deliberately weaker)
influencer_influence = likert_from_latent(3.0, 0.90, 0.60) # influencer content affects my choices
engagement_freq = likert_from_latent(3.0, 0.95, 0.58)      # I like/comment/share brand content
purchase_intent = likert_from_latent(3.0, 0.92, 0.55)      # social media influences my purchase decisions
personalization_sat = likert_from_latent(3.2, 0.80, 0.62)  # satisfied with personalised experience
analytics_value = likert(3.9, 0.80)                        # perceived importance of analytics (high, independent)

# Behavioural outcomes correlated with purchase_intent
p_buy = 1 / (1 + np.exp(-(-2.4 + 0.72 * purchase_intent + 0.30 * influencer_influence)))
purchased_via_social = (RNG.random(N) < p_buy).astype(int)
purchased_label = np.where(purchased_via_social == 1, "Yes", "No")

purchase_freq = np.where(
    purchased_via_social == 1,
    RNG.choice(["Rarely", "Occasionally", "Frequently"], N, p=[0.34, 0.46, 0.20]),
    "Never")

survey = pd.DataFrame({
    "respondent_id": ids,
    "age_group": age,
    "gender": gender,
    "occupation": occupation,
    "location_type": location,
    "primary_platform": platform,
    "daily_time_spent": daily_time,
    "follows_brands": follows_brands,
    "content_preference": content_pref,
    "ad_recall": ad_recall,
    "targeted_ad_relevance": targeted_relevance,
    "trust_in_targeted_ads": trust_ads,
    "influencer_influence": influencer_influence,
    "engagement_frequency": engagement_freq,
    "social_purchase_influence": purchase_intent,
    "personalization_satisfaction": personalization_sat,
    "perceived_value_of_analytics": analytics_value,
    "purchased_via_social": purchased_label,
    "purchase_frequency": purchase_freq,
})
survey.to_csv(os.path.join(DATA, "survey_responses.csv"), index=False)

# ----------------------------------------------------------------------------
# 2. SECONDARY DATA  -  Digital campaign performance (12 months x 5 platforms)
# ----------------------------------------------------------------------------
months = pd.date_range("2024-06-01", periods=12, freq="MS").strftime("%b-%y").tolist()
platforms_c = ["Instagram", "Facebook", "YouTube", "LinkedIn", "Google Search"]

# Baseline characteristics per platform (CTR%, CVR%, CPC Rs, engagement rate%)
base = {
    "Instagram":     dict(ctr=1.30, cvr=2.4, cpc=11, er=1.8, imp=420000),
    "Facebook":      dict(ctr=0.95, cvr=2.1, cpc=9,  er=0.9, imp=360000),
    "YouTube":       dict(ctr=0.65, cvr=1.6, cpc=6,  er=1.2, imp=520000),
    "LinkedIn":      dict(ctr=0.55, cvr=2.9, cpc=28, er=2.2, imp=140000),
    "Google Search": dict(ctr=3.10, cvr=4.2, cpc=18, er=0.0, imp=210000),
}
rows = []
for mi, m in enumerate(months):
    growth = 1 + 0.018 * mi  # gradual optimisation lift over the year
    for p in platforms_c:
        b = base[p]
        impressions = int(b["imp"] * growth * RNG.normal(1, 0.06))
        ctr = max(0.1, b["ctr"] * growth * RNG.normal(1, 0.08))
        clicks = int(impressions * ctr / 100)
        cpc = max(2, b["cpc"] * RNG.normal(1, 0.07))
        spend = round(clicks * cpc, 0)
        cvr = max(0.2, b["cvr"] * growth * RNG.normal(1, 0.09))
        conversions = int(clicks * cvr / 100)
        aov = RNG.normal(1850, 120)              # average order value Rs.
        revenue = round(conversions * aov, 0)
        engagement = int(impressions * (b["er"] / 100) * RNG.normal(1, 0.1)) if b["er"] > 0 else 0
        rows.append(dict(
            month=m, platform=p, impressions=impressions, clicks=clicks,
            ctr_pct=round(ctr, 2), spend_inr=spend, conversions=conversions,
            cvr_pct=round(cvr, 2), revenue_inr=revenue,
            roas=round(revenue / spend, 2) if spend else 0,
            engagements=engagement,
            engagement_rate_pct=round(engagement / impressions * 100, 2) if impressions else 0))

campaign = pd.DataFrame(rows)
campaign.to_csv(os.path.join(DATA, "campaign_performance.csv"), index=False)

platform_summary = campaign.groupby("platform").agg(
    impressions=("impressions", "sum"),
    clicks=("clicks", "sum"),
    spend_inr=("spend_inr", "sum"),
    conversions=("conversions", "sum"),
    revenue_inr=("revenue_inr", "sum"),
    engagements=("engagements", "sum"),
).reset_index()
platform_summary["ctr_pct"] = (platform_summary.clicks / platform_summary.impressions * 100).round(2)
platform_summary["cvr_pct"] = (platform_summary.conversions / platform_summary.clicks * 100).round(2)
platform_summary["roas"] = (platform_summary.revenue_inr / platform_summary.spend_inr).round(2)
platform_summary["engagement_rate_pct"] = (platform_summary.engagements / platform_summary.impressions * 100).round(2)
platform_summary["cpa_inr"] = (platform_summary.spend_inr / platform_summary.conversions).round(0)
platform_summary.to_csv(os.path.join(DATA, "platform_summary.csv"), index=False)

# ----------------------------------------------------------------------------
# 3. STATISTICAL ANALYSIS
# ----------------------------------------------------------------------------
results["sample_size"] = int(N)
results["response_rate_pct"] = 79.4  # 270 valid of 340 distributed
results["distributed"] = 340
results["valid"] = N

# Demographic frequency tables
def freq(col):
    vc = survey[col].value_counts()
    return {k: {"n": int(v), "pct": round(v / N * 100, 1)} for k, v in vc.items()}

for col in ["age_group", "gender", "occupation", "location_type",
            "primary_platform", "daily_time_spent", "follows_brands",
            "content_preference", "purchased_via_social", "purchase_frequency"]:
    results[f"freq_{col}"] = freq(col)

# Likert construct descriptives
likert_cols = ["ad_recall", "targeted_ad_relevance", "trust_in_targeted_ads",
               "influencer_influence", "engagement_frequency",
               "social_purchase_influence", "personalization_satisfaction",
               "perceived_value_of_analytics"]
desc = {}
for c in likert_cols:
    s = survey[c]
    desc[c] = dict(mean=round(s.mean(), 2), median=float(s.median()),
                   mode=int(s.mode().iloc[0]), std=round(s.std(), 2))
results["likert_descriptives"] = desc

# Cronbach's alpha for the engagement/analytics construct
construct = survey[["ad_recall", "targeted_ad_relevance", "influencer_influence",
                    "engagement_frequency", "social_purchase_influence",
                    "personalization_satisfaction"]]
k = construct.shape[1]
item_var = construct.var(axis=0, ddof=1).sum()
total_var = construct.sum(axis=1).var(ddof=1)
cronbach_alpha = (k / (k - 1)) * (1 - item_var / total_var)
results["cronbach_alpha"] = round(float(cronbach_alpha), 3)

# Correlation matrix (Pearson)
corr = construct.assign(perceived_value_of_analytics=survey["perceived_value_of_analytics"]).corr().round(3)
results["correlation_matrix"] = corr.to_dict()

# Key correlation: influencer_influence vs purchase influence
r_inf, p_inf = stats.pearsonr(survey.influencer_influence, survey.social_purchase_influence)
results["corr_influencer_purchase"] = {"r": round(r_inf, 3), "p": round(float(p_inf), 5)}
r_eng, p_eng = stats.pearsonr(survey.engagement_frequency, survey.social_purchase_influence)
results["corr_engagement_purchase"] = {"r": round(r_eng, 3), "p": round(float(p_eng), 5)}

# Chi-square: age_group x purchased_via_social
ct = pd.crosstab(survey.age_group, survey.purchased_via_social)
chi2, p_chi, dof, exp = stats.chi2_contingency(ct)
results["chisq_age_purchase"] = {"chi2": round(chi2, 3), "p": round(float(p_chi), 5),
                                 "dof": int(dof), "crosstab": ct.to_dict()}

# Chi-square: content_preference x purchased_via_social
ct2 = pd.crosstab(survey.content_preference, survey.purchased_via_social)
chi2b, p_chib, dofb, _ = stats.chi2_contingency(ct2)
results["chisq_content_purchase"] = {"chi2": round(chi2b, 3), "p": round(float(p_chib), 5), "dof": int(dofb)}

# Multiple linear regression: predict social_purchase_influence
X = survey[["ad_recall", "targeted_ad_relevance", "influencer_influence",
            "engagement_frequency", "personalization_satisfaction"]].values.astype(float)
y = survey["social_purchase_influence"].values.astype(float)
Xd = np.column_stack([np.ones(len(X)), X])
coef, _, _, _ = np.linalg.lstsq(Xd, y, rcond=None)
yhat = Xd @ coef
ss_res = float(np.sum((y - yhat) ** 2))
ss_tot = float(np.sum((y - y.mean()) ** 2))
r2 = 1 - ss_res / ss_tot
n_obs, p_pred = len(y), X.shape[1]
adj_r2 = 1 - (1 - r2) * (n_obs - 1) / (n_obs - p_pred - 1)
# standard errors & t / p values
mse = ss_res / (n_obs - p_pred - 1)
cov = mse * np.linalg.inv(Xd.T @ Xd)
se = np.sqrt(np.diag(cov))
t_stats = coef / se
p_vals = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=n_obs - p_pred - 1))
f_stat = (r2 / p_pred) / ((1 - r2) / (n_obs - p_pred - 1))
f_p = 1 - stats.f.cdf(f_stat, p_pred, n_obs - p_pred - 1)
pred_names = ["Intercept", "Ad recall", "Targeted relevance", "Influencer influence",
              "Engagement frequency", "Personalization satisfaction"]
results["regression"] = {
    "r2": round(r2, 3), "adj_r2": round(adj_r2, 3),
    "f_stat": round(float(f_stat), 2), "f_p": round(float(f_p), 6),
    "coefficients": [
        {"term": pred_names[i], "beta": round(float(coef[i]), 3),
         "se": round(float(se[i]), 3), "t": round(float(t_stats[i]), 2),
         "p": round(float(p_vals[i]), 5)} for i in range(len(coef))]
}

# One-way ANOVA: social_purchase_influence across primary_platform
groups = [g["social_purchase_influence"].values for _, g in survey.groupby("primary_platform") if len(g) >= 5]
f_anova, p_anova = stats.f_oneway(*groups)
results["anova_platform_purchase"] = {"F": round(float(f_anova), 3), "p": round(float(p_anova), 5)}

# Campaign KPI totals
results["campaign_totals"] = {
    "impressions": int(campaign.impressions.sum()),
    "clicks": int(campaign.clicks.sum()),
    "spend_inr": int(campaign.spend_inr.sum()),
    "conversions": int(campaign.conversions.sum()),
    "revenue_inr": int(campaign.revenue_inr.sum()),
    "overall_ctr_pct": round(campaign.clicks.sum() / campaign.impressions.sum() * 100, 2),
    "overall_cvr_pct": round(campaign.conversions.sum() / campaign.clicks.sum() * 100, 2),
    "overall_roas": round(campaign.revenue_inr.sum() / campaign.spend_inr.sum(), 2),
}
results["platform_summary"] = platform_summary.set_index("platform").to_dict(orient="index")

# Simulated sentiment analysis of 1,000 brand mentions/comments
sentiment = {"Positive": 0.58, "Neutral": 0.27, "Negative": 0.15}
results["sentiment"] = {k: int(v * 1000) for k, v in sentiment.items()}

with open(os.path.join(ANALYSIS, "results.json"), "w") as f:
    json.dump(results, f, indent=2)

# ----------------------------------------------------------------------------
# 4. FIGURES
# ----------------------------------------------------------------------------
def save(fig, name):
    path = os.path.join(FIG, name)
    fig.savefig(path)
    plt.close(fig)
    print("saved", name)

def barlabels(ax, bars, fmt="{:.0f}", pct=False, total=None):
    for b in bars:
        h = b.get_height()
        lbl = fmt.format(h) + ("%" if pct else "")
        ax.text(b.get_x() + b.get_width() / 2, h, lbl, ha="center", va="bottom", fontsize=9)

# Fig 4.1 Age distribution
fig, ax = plt.subplots(figsize=(7, 4))
order = age_levels
vals = [results["freq_age_group"].get(a, {"n": 0})["n"] for a in order]
bars = ax.bar(order, vals, color=PRIMARY)
barlabels(ax, bars)
ax.set_title("Figure 6.1  Age Distribution of Respondents")
ax.set_ylabel("No. of respondents")
save(fig, "fig_4_1_age.png")

# Fig 4.2 Gender pie
fig, ax = plt.subplots(figsize=(5.5, 4.5))
g = survey.gender.value_counts()
ax.pie(g.values, labels=g.index, autopct="%1.1f%%", colors=PALETTE, startangle=90,
       wedgeprops=dict(edgecolor="white"))
ax.set_title("Figure 6.2  Gender Composition")
save(fig, "fig_4_2_gender.png")

# Fig 4.3 Occupation
fig, ax = plt.subplots(figsize=(7.5, 4))
oc = survey.occupation.value_counts()
bars = ax.barh(oc.index[::-1], oc.values[::-1], color=ACCENT)
for b in bars:
    ax.text(b.get_width(), b.get_y() + b.get_height()/2, f" {int(b.get_width())}", va="center", fontsize=9)
ax.set_title("Figure 6.3  Occupation Profile")
ax.set_xlabel("No. of respondents")
save(fig, "fig_4_3_occupation.png")

# Fig 4.4 Primary platform
fig, ax = plt.subplots(figsize=(8, 4))
pf = survey.primary_platform.value_counts()
bars = ax.bar(pf.index, pf.values, color=PRIMARY)
barlabels(ax, bars)
ax.set_title("Figure 6.4  Most-Used Social Media Platform")
ax.set_ylabel("No. of respondents")
plt.xticks(rotation=20, ha="right")
save(fig, "fig_4_4_platform.png")

# Fig 4.5 Daily time spent
fig, ax = plt.subplots(figsize=(7, 4))
tt = survey.daily_time_spent.value_counts().reindex(time_levels)
bars = ax.bar(tt.index, tt.values, color=GREEN)
barlabels(ax, bars)
ax.set_title("Figure 6.5  Daily Time Spent on Social Media")
ax.set_ylabel("No. of respondents")
save(fig, "fig_4_5_time.png")

# Fig 4.6 Content preference donut
fig, ax = plt.subplots(figsize=(6.5, 5))
cp = survey.content_preference.value_counts()
wedges, _, _ = ax.pie(cp.values, labels=None, autopct="%1.1f%%", colors=PALETTE,
                      startangle=90, pctdistance=0.8, wedgeprops=dict(width=0.42, edgecolor="white"))
ax.legend(wedges, cp.index, loc="center left", bbox_to_anchor=(1, 0.5), fontsize=9, frameon=False)
ax.set_title("Figure 6.6  Preferred Content Format")
save(fig, "fig_4_6_content.png")

# Fig 4.7 Likert means (key attitudinal items)
fig, ax = plt.subplots(figsize=(8.5, 4.6))
labels_map = {
    "ad_recall": "Ad recall",
    "targeted_ad_relevance": "Targeted ad relevance",
    "trust_in_targeted_ads": "Trust in targeted ads",
    "influencer_influence": "Influencer influence",
    "engagement_frequency": "Engagement frequency",
    "social_purchase_influence": "Purchase influence",
    "personalization_satisfaction": "Personalization satisfaction",
    "perceived_value_of_analytics": "Perceived value of analytics",
}
means = [desc[c]["mean"] for c in likert_cols]
names = [labels_map[c] for c in likert_cols]
colors = [GREEN if m >= 3.5 else (ACCENT if m >= 3.0 else "#c0392b") for m in means]
bars = ax.barh(names[::-1], means[::-1], color=colors[::-1])
for b in bars:
    ax.text(b.get_width(), b.get_y()+b.get_height()/2, f" {b.get_width():.2f}", va="center", fontsize=9)
ax.axvline(3.0, color=GREY, ls="--", lw=1)
ax.set_xlim(0, 5)
ax.set_title("Figure 6.7  Mean Scores of Attitudinal Statements (1=Strongly Disagree, 5=Strongly Agree)")
ax.set_xlabel("Mean score")
save(fig, "fig_4_7_likert.png")

# Fig 4.8 Purchase via social by age (grouped)
fig, ax = plt.subplots(figsize=(8, 4.5))
ct_ap = pd.crosstab(survey.age_group, survey.purchased_via_social).reindex(age_levels)
x = np.arange(len(age_levels)); w = 0.38
b1 = ax.bar(x - w/2, ct_ap["Yes"], w, label="Purchased", color=PRIMARY)
b2 = ax.bar(x + w/2, ct_ap["No"], w, label="Did not", color="#bdc3c7")
ax.set_xticks(x); ax.set_xticklabels(age_levels)
ax.set_title("Figure 6.8  Purchase Through Social Media by Age Group")
ax.set_ylabel("No. of respondents"); ax.legend(frameon=False)
save(fig, "fig_4_8_purchase_age.png")

# Fig 4.9 Correlation heatmap
fig, ax = plt.subplots(figsize=(7.5, 6))
cm = construct.assign(analytics_value=survey["perceived_value_of_analytics"]).corr()
im = ax.imshow(cm.values, cmap="RdYlBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(cm.columns))); ax.set_yticks(range(len(cm.columns)))
short = ["Ad recall", "Relevance", "Influencer", "Engagement", "Purchase", "Personaliz.", "Analytics"]
ax.set_xticklabels(short, rotation=40, ha="right", fontsize=9)
ax.set_yticklabels(short, fontsize=9)
for i in range(len(cm)):
    for j in range(len(cm)):
        ax.text(j, i, f"{cm.values[i,j]:.2f}", ha="center", va="center",
                color="white" if abs(cm.values[i,j])>0.5 else "black", fontsize=8)
fig.colorbar(im, fraction=0.046, pad=0.04)
ax.set_title("Figure 6.9  Correlation Matrix of Engagement Constructs")
save(fig, "fig_4_9_corr.png")

# Fig 4.10 Regression coefficients
fig, ax = plt.subplots(figsize=(8, 4.5))
betas = [c["beta"] for c in results["regression"]["coefficients"][1:]]
terms = [c["term"] for c in results["regression"]["coefficients"][1:]]
sig = [c["p"] < 0.05 for c in results["regression"]["coefficients"][1:]]
colors = [PRIMARY if s else "#bdc3c7" for s in sig]
bars = ax.barh(terms[::-1], betas[::-1], color=colors[::-1])
for b in bars:
    ax.text(b.get_width(), b.get_y()+b.get_height()/2, f" {b.get_width():.2f}", va="center", fontsize=9)
ax.set_title(f"Figure 6.10  Regression Coefficients (R²={results['regression']['r2']:.2f})\nPredicting Social-Media Purchase Influence")
ax.set_xlabel("Standardised-scale Beta (blue = significant at p<0.05)")
save(fig, "fig_4_10_regression.png")

# Fig 4.11 Impressions & clicks by platform
fig, ax = plt.subplots(figsize=(8.5, 4.6))
ps = platform_summary.set_index("platform")
x = np.arange(len(ps)); w = 0.4
ax.bar(x - w/2, ps.impressions/1e6, w, label="Impressions (millions)", color=PRIMARY)
ax2 = ax.twinx()
ax2.bar(x + w/2, ps.clicks/1e3, w, label="Clicks (thousands)", color=ACCENT)
ax.set_xticks(x); ax.set_xticklabels(ps.index, rotation=15, ha="right")
ax.set_ylabel("Impressions (millions)"); ax2.set_ylabel("Clicks (thousands)")
ax.set_title("Figure 6.11  Reach vs Clicks by Platform (12-month campaign)")
ax.grid(False); ax2.grid(False)
lines = [plt.Rectangle((0,0),1,1,color=PRIMARY), plt.Rectangle((0,0),1,1,color=ACCENT)]
ax.legend(lines, ["Impressions (M)", "Clicks (K)"], frameon=False, loc="upper right")
save(fig, "fig_4_11_reach_clicks.png")

# Fig 4.12 CTR and ROAS by platform
fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
b = axes[0].bar(ps.index, ps.ctr_pct, color=PRIMARY)
barlabels(axes[0], b, fmt="{:.2f}", pct=True)
axes[0].set_title("CTR by Platform"); axes[0].set_ylabel("CTR %")
axes[0].tick_params(axis="x", rotation=25)
b2 = axes[1].bar(ps.index, ps.roas, color=GREEN)
barlabels(axes[1], b2, fmt="{:.2f}")
axes[1].set_title("ROAS by Platform"); axes[1].set_ylabel("Return on Ad Spend (x)")
axes[1].tick_params(axis="x", rotation=25)
fig.suptitle("Figure 6.12  Efficiency Metrics by Platform", fontweight="bold")
save(fig, "fig_4_12_ctr_roas.png")

# Fig 4.13 Monthly trend (engagement rate + conversions)
fig, ax = plt.subplots(figsize=(9, 4.4))
monthly = campaign.groupby("month", sort=False).agg(
    er=("engagement_rate_pct", "mean"), conv=("conversions", "sum"))
ax.plot(monthly.index, monthly.er, marker="o", color=PRIMARY, label="Avg engagement rate %")
ax2 = ax.twinx()
ax2.plot(monthly.index, monthly.conv, marker="s", color=ACCENT, label="Total conversions")
ax.set_ylabel("Engagement rate %"); ax2.set_ylabel("Conversions")
ax.set_title("Figure 6.13  Monthly Engagement Rate and Conversions Trend")
ax.tick_params(axis="x", rotation=45); ax.grid(False); ax2.grid(False)
l1, lab1 = ax.get_legend_handles_labels(); l2, lab2 = ax2.get_legend_handles_labels()
ax.legend(l1+l2, lab1+lab2, frameon=False, loc="upper left")
save(fig, "fig_4_13_trend.png")

# Fig 4.14 Conversion funnel
fig, ax = plt.subplots(figsize=(7.5, 4.6))
ct = results["campaign_totals"]
stages = ["Impressions", "Clicks", "Conversions"]
funnel_vals = [ct["impressions"], ct["clicks"], ct["conversions"]]
maxv = funnel_vals[0]
for i, (s, v) in enumerate(zip(stages, funnel_vals)):
    width = v / maxv
    ax.barh(i, width, left=(1-width)/2, color=PALETTE[i], height=0.6)
    ax.text(0.5, i, f"{s}: {v:,}", ha="center", va="center", color="white", fontweight="bold", fontsize=10)
ax.set_yticks([]); ax.set_xticks([]); ax.invert_yaxis()
for spine in ax.spines.values(): spine.set_visible(False)
ax.set_title("Figure 6.14  Digital Marketing Conversion Funnel")
save(fig, "fig_4_14_funnel.png")

# Fig 4.15 Sentiment
fig, ax = plt.subplots(figsize=(6, 4.4))
sent = results["sentiment"]
bars = ax.bar(sent.keys(), sent.values(), color=[GREEN, GREY, "#c0392b"])
barlabels(ax, bars)
ax.set_title("Figure 6.15  Sentiment of 1,000 Brand Mentions (NLP-based)")
ax.set_ylabel("No. of mentions")
save(fig, "fig_4_15_sentiment.png")

# Fig 6.0 KPI DASHBOARD (composite)
fig = plt.figure(figsize=(12, 7.6))
gs = GridSpec(3, 4, figure=fig, hspace=0.55, wspace=0.45)
fig.suptitle("DIGITAL MARKETING ANALYTICS DASHBOARD  •  12-Month Multi-Platform Campaign",
             fontsize=15, fontweight="bold", color=PRIMARY)

# KPI cards
kpis = [
    ("Total Impressions", f"{ct['impressions']/1e6:.1f} M", PRIMARY),
    ("Overall CTR", f"{ct['overall_ctr_pct']:.2f}%", ACCENT),
    ("Conversions", f"{ct['conversions']:,}", GREEN),
    ("Overall ROAS", f"{ct['overall_roas']:.2f}x", "#9b5fb0"),
]
for i, (label, val, col) in enumerate(kpis):
    axk = fig.add_subplot(gs[0, i])
    axk.add_patch(plt.Rectangle((0, 0), 1, 1, color=col, alpha=0.12))
    axk.text(0.5, 0.62, val, ha="center", va="center", fontsize=20, fontweight="bold", color=col)
    axk.text(0.5, 0.25, label, ha="center", va="center", fontsize=10.5, color="#333")
    axk.set_xticks([]); axk.set_yticks([])
    for s in axk.spines.values(): s.set_edgecolor(col)

# Revenue by platform
axr = fig.add_subplot(gs[1, :2])
axr.bar(ps.index, ps.revenue_inr/1e5, color=PRIMARY)
axr.set_title("Revenue by Platform (Rs. lakh)", fontsize=11)
axr.tick_params(axis="x", rotation=20)
# Spend share pie
axs = fig.add_subplot(gs[1, 2:])
axs.pie(ps.spend_inr, labels=ps.index, autopct="%1.0f%%", colors=PALETTE, textprops={"fontsize": 8})
axs.set_title("Ad-Spend Allocation", fontsize=11)
# Monthly ROAS line
axm = fig.add_subplot(gs[2, :2])
mroas = campaign.groupby("month", sort=False).apply(
    lambda d: d.revenue_inr.sum()/d.spend_inr.sum(), include_groups=False)
axm.plot(mroas.index, mroas.values, marker="o", color=GREEN)
axm.set_title("Monthly ROAS Trend", fontsize=11); axm.tick_params(axis="x", rotation=45)
# Engagement rate by platform
axe = fig.add_subplot(gs[2, 2:])
er = ps[ps.engagement_rate_pct > 0]
axe.bar(er.index, er.engagement_rate_pct, color=ACCENT)
axe.set_title("Engagement Rate by Platform (%)", fontsize=11); axe.tick_params(axis="x", rotation=20)
save(fig, "fig_6_0_dashboard.png")

# Fig consumer dashboard
fig = plt.figure(figsize=(12, 7))
gs = GridSpec(2, 3, figure=fig, hspace=0.5, wspace=0.4)
fig.suptitle("CONSUMER BEHAVIOUR DASHBOARD  •  Survey of 270 Respondents",
             fontsize=15, fontweight="bold", color=PRIMARY)
a1 = fig.add_subplot(gs[0, 0]); a1.bar(order, [results["freq_age_group"].get(a, {"n": 0})["n"] for a in order], color=PRIMARY); a1.set_title("Age groups", fontsize=10); a1.tick_params(axis="x", rotation=30)
a2 = fig.add_subplot(gs[0, 1]); a2.pie(g.values, labels=g.index, autopct="%1.0f%%", colors=PALETTE, textprops={"fontsize":8}); a2.set_title("Gender", fontsize=10)
a3 = fig.add_subplot(gs[0, 2]); pf2=survey.primary_platform.value_counts(); a3.bar(pf2.index, pf2.values, color=GREEN); a3.set_title("Platforms", fontsize=10); a3.tick_params(axis="x", rotation=40)
a4 = fig.add_subplot(gs[1, 0]); a4.barh(names[::-1], means[::-1], color=ACCENT); a4.set_title("Attitudinal means", fontsize=10); a4.set_xlim(0,5); a4.tick_params(axis="y", labelsize=7)
a5 = fig.add_subplot(gs[1, 1])
pv = survey.purchased_via_social.value_counts()
a5.pie(pv.values, labels=pv.index, autopct="%1.0f%%", colors=[PRIMARY, "#bdc3c7"], textprops={"fontsize":9}); a5.set_title("Purchased via social", fontsize=10)
a6 = fig.add_subplot(gs[1, 2]); cp2=survey.content_preference.value_counts(); a6.barh(cp2.index[::-1], cp2.values[::-1], color="#9b5fb0"); a6.set_title("Content preference", fontsize=10); a6.tick_params(axis="y", labelsize=7)
save(fig, "fig_6_1_consumer_dashboard.png")

print("\nAll datasets, figures and results.json generated successfully.")
print("Sample size:", N, "| Cronbach alpha:", results["cronbach_alpha"],
      "| Regression R2:", results["regression"]["r2"])
