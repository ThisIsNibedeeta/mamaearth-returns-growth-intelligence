from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "visualizations"
OUT.mkdir(exist_ok=True)

orders = pd.read_csv(DATA / "orders.csv")
customers = pd.read_csv(DATA / "customers.csv")
products = pd.read_csv(DATA / "products.csv")

orders["payment_method"] = orders["payment_method"].str.strip().str.upper()
natural_key = [
    "customer_id", "product_id", "order_date", "quantity",
    "discount_pct", "payment_method", "rating", "returned"
]
orders = orders.loc[~orders.duplicated(subset=natural_key, keep="first")].copy()
orders["discount_pct"] = orders["discount_pct"].fillna(0)
orders["rating"] = orders["rating"].fillna(orders["rating"].median())

merged = (
    orders.merge(products, on="product_id", how="left")
          .merge(customers, on="customer_id", how="left")
)
merged["order_value"] = (
    merged["quantity"] * merged["price"] *
    (1 - merged["discount_pct"] / 100.0)
)

payment_rate = merged.groupby("payment_method")["returned"].mean().mul(100).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(payment_rate.index, payment_rate.values)
ax.set_xlabel("Payment Method")
ax.set_ylabel("Return Rate (%)")
ax.set_title("COD Returns at 44.4% — 3x Card")
for bar, value in zip(bars, payment_rate.values):
    ax.text(bar.get_x() + bar.get_width()/2, value + 1, f"{value:.1f}%", ha="center")
ax.set_ylim(0, max(payment_rate.values) * 1.18)
fig.tight_layout()
fig.savefig(OUT / "return_rate_by_payment.png", dpi=150)
plt.close(fig)

merged["order_date"] = pd.to_datetime(merged["order_date"])
merged["year_month"] = merged["order_date"].dt.to_period("M").astype(str)
merged["is_outlier"] = ~merged["quantity"].between(
    merged["quantity"].quantile(0.25) - 1.5 * (merged["quantity"].quantile(0.75) - merged["quantity"].quantile(0.25)),
    merged["quantity"].quantile(0.75) + 1.5 * (merged["quantity"].quantile(0.75) - merged["quantity"].quantile(0.25))
)
monthly = merged.loc[~merged["is_outlier"]].groupby("year_month")["order_value"].sum().round(2)
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(monthly.index, monthly.values, marker="o")
ax.set_xlabel("Month")
ax.set_ylabel("Revenue (INR)")
ax.set_title("Outlier-Corrected Monthly Revenue — Peak: March 2026")
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(OUT / "monthly_revenue_trend.png", dpi=150)
plt.close(fig)

print("Saved:", OUT / "return_rate_by_payment.png")
print("Saved:", OUT / "monthly_revenue_trend.png")
