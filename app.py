import streamlit as st
import pandas as pd
import os
from datetime import datetime

DATA_FILE = "budget_data.csv"
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

CATEGORIES = ["God", "Investment", "Savings", "Bills", "Upkeep"]
DEFAULT_PCT = {"God": 10, "Investment": 40, "Savings": 35, "Bills": 8, "Upkeep": 7}

st.set_page_config(page_title="Monthly Budget Tracker", layout="wide")


def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    cols = ["Year", "Month", "Income"] + CATEGORIES + ["Notes", "LastUpdated"]
    return pd.DataFrame(columns=cols)


def save_data(df):
    df.to_csv(DATA_FILE, index=False)


st.title("Monthly Budget Allocator")
st.caption("Divide your monthly income across categories, tracked every month, every year.")

# ---------------- Sidebar: percentage settings ----------------
st.sidebar.header("Allocation Percentages")
st.sidebar.write("Adjust these to match your real split.")

pct = {}
for cat in CATEGORIES:
    pct[cat] = st.sidebar.number_input(
        f"{cat} (%)", min_value=0.0, max_value=100.0,
        value=float(DEFAULT_PCT[cat]), step=0.5, key=f"pct_{cat}"
    )

total_pct = sum(pct.values())
if abs(total_pct - 100) > 0.01:
    st.sidebar.warning(f"Your percentages add up to {total_pct:.1f}%, not 100%. "
                        f"{100 - total_pct:.1f}% of your income has no category.")
else:
    st.sidebar.success("Percentages add up to 100%.")

df = load_data()

# ---------------- Entry form ----------------
st.subheader("Add / Update a Month")

col1, col2, col3 = st.columns(3)
with col1:
    year = st.number_input("Year", min_value=2020, max_value=2100,
                            value=datetime.now().year, step=1)
with col2:
    month = st.selectbox("Month", MONTHS)
with col3:
    income = st.number_input("Total income this month (₦)", min_value=0.0, step=10000.0)

notes = st.text_input("Notes (optional)")

if st.button("Save this month", type="primary"):
    amounts = {cat: round(income * pct[cat] / 100, 2) for cat in CATEGORIES}
    mask = (df["Year"] == year) & (df["Month"] == month)
    row = {"Year": year, "Month": month, "Income": income, **amounts,
           "Notes": notes, "LastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M")}
    if mask.any():
        for k, v in row.items():
            df.loc[mask, k] = v
        st.success(f"Updated {month} {year}.")
    else:
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        st.success(f"Saved {month} {year}.")
    save_data(df)

# ---------------- Yearly view ----------------
st.subheader(f"Overview for {year}")

year_df = df[df["Year"] == year].copy()
if not year_df.empty:
    year_df["Month"] = pd.Categorical(year_df["Month"], categories=MONTHS, ordered=True)
    year_df = year_df.sort_values("Month")
    display_cols = ["Month", "Income"] + CATEGORIES + ["Notes"]
    st.dataframe(year_df[display_cols], use_container_width=True, hide_index=True)

    totals = year_df[["Income"] + CATEGORIES].sum()
    st.markdown("**Year totals so far:**")
    cols = st.columns(len(CATEGORIES) + 1)
    cols[0].metric("Total Income", f"₦{totals['Income']:,.0f}")
    for i, cat in enumerate(CATEGORIES, start=1):
        cols[i].metric(cat, f"₦{totals[cat]:,.0f}")

    st.markdown("**Allocation by month**")
    chart_df = year_df.set_index("Month")[CATEGORIES]
    st.bar_chart(chart_df)
else:
    st.info(f"No entries yet for {year}. Add a month above to get started.")

# ---------------- All-time data + export ----------------
with st.expander("View all saved data / export"):
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download all data as CSV", csv, "budget_data.csv", "text/csv")
    else:
        st.write("No data saved yet.")
