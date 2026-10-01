import streamlit as st
import pandas as pd
import os
from datetime import datetime

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

CATEGORIES = ["God", "Investment", "Savings", "Bills", "Upkeep"]
DEFAULT_PCT = {"God": 10, "Investment": 40, "Savings": 35, "Bills": 8, "Upkeep": 7}

st.set_page_config(page_title="Monthly Budget Tracker", layout="wide")


def load_data(data_file):
    if os.path.exists(data_file):
        return pd.read_csv(data_file)
    cols = ["Year", "Month", "Income"] + CATEGORIES + ["Notes", "LastUpdated"]
    return pd.DataFrame(columns=cols)


def save_data(df, data_file):
    df.to_csv(data_file, index=False)


def fmt(symbol, value):
    """Format a number with thousands separators and a currency symbol."""
    try:
        return f"{symbol}{float(value):,.0f}"
    except (ValueError, TypeError):
        return value


def render_section(currency_name, symbol, data_file, key_prefix):
    st.header(f"{currency_name} Savings")

    # ---------------- Sidebar: percentage settings ----------------
    st.sidebar.subheader(f"{currency_name} Allocation Percentages")
    pct = {}
    for cat in CATEGORIES:
        pct[cat] = st.sidebar.number_input(
            f"{cat} (%)", min_value=0.0, max_value=100.0,
            value=float(DEFAULT_PCT[cat]), step=0.5, key=f"{key_prefix}_pct_{cat}"
        )
    total_pct = sum(pct.values())
    if abs(total_pct - 100) > 0.01:
        st.sidebar.warning(f"{currency_name}: percentages add up to {total_pct:.1f}%, not 100%. "
                            f"{100 - total_pct:.1f}% has no category.")
    else:
        st.sidebar.success(f"{currency_name}: percentages add up to 100%.")

    df = load_data(data_file)

    # ---------------- Entry form ----------------
    st.subheader("Add / Update a Month")
    col1, col2, col3 = st.columns(3)
    with col1:
        year = st.number_input("Year", min_value=2020, max_value=2100,
                                value=datetime.now().year, step=1, key=f"{key_prefix}_year")
    with col2:
        month = st.selectbox("Month", MONTHS, key=f"{key_prefix}_month")
    with col3:
        income = st.number_input(f"Total income this month ({symbol})", min_value=0.0,
                                  step=10000.0, key=f"{key_prefix}_income")

    notes = st.text_input("Notes (optional)", key=f"{key_prefix}_notes")

    if st.button("Save this month", type="primary", key=f"{key_prefix}_save"):
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
        save_data(df, data_file)

    # ---------------- Yearly view ----------------
    st.subheader(f"Overview for {year}")
    year_df = df[df["Year"] == year].copy()

    if not year_df.empty:
        year_df["Month"] = pd.Categorical(year_df["Month"], categories=MONTHS, ordered=True)
        year_df = year_df.sort_values("Month")

        display_df = year_df[["Month", "Income"] + CATEGORIES + ["Notes"]].copy()
        for col in ["Income"] + CATEGORIES:
            display_df[col] = display_df[col].apply(lambda v: fmt(symbol, v))
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        totals = year_df[["Income"] + CATEGORIES].sum()
        st.markdown("**Year totals so far:**")
        cols = st.columns(len(CATEGORIES) + 1)
        cols[0].metric("Total Income", fmt(symbol, totals["Income"]))
        for i, cat in enumerate(CATEGORIES, start=1):
            cols[i].metric(cat, fmt(symbol, totals[cat]))

        st.markdown("**Allocation by month**")
        chart_df = year_df.set_index("Month")[CATEGORIES]
        st.bar_chart(chart_df)
    else:
        st.info(f"No entries yet for {year}. Add a month above to get started.")

    # ---------------- Delete data ----------------
    st.subheader("Delete Data")
    del_col1, del_col2 = st.columns(2)

    with del_col1:
        st.markdown("**Delete a single month**")
        if not df.empty:
            existing = df.apply(lambda r: f"{r['Month']} {int(r['Year'])}", axis=1).tolist()
            choice = st.selectbox("Select entry to delete", ["-- choose --"] + existing,
                                   key=f"{key_prefix}_del_month")
            if choice != "-- choose --":
                confirm = st.checkbox(f"I confirm I want to delete {choice}",
                                       key=f"{key_prefix}_confirm_month")
                if st.button("Delete this month", key=f"{key_prefix}_btn_del_month"):
                    if confirm:
                        sel_month, sel_year = choice.rsplit(" ", 1)
                        df = df[~((df["Year"] == int(sel_year)) & (df["Month"] == sel_month))]
                        save_data(df, data_file)
                        st.session_state.pop(f"{key_prefix}_del_month", None)
                        st.session_state.pop(f"{key_prefix}_confirm_month", None)
                        st.success(f"Deleted {choice}.")
                        st.rerun()
                    else:
                        st.warning("Please check the confirmation box first.")
        else:
            st.write("No entries to delete.")

    with del_col2:
        st.markdown("**Delete a whole year**")
        if not df.empty:
            years_present = sorted(df["Year"].unique().tolist())
            year_choice = st.selectbox("Select year to clear", ["-- choose --"] + years_present,
                                        key=f"{key_prefix}_del_year")
            if year_choice != "-- choose --":
                confirm_year = st.checkbox(f"I confirm I want to delete ALL {year_choice} data",
                                            key=f"{key_prefix}_confirm_year")
                if st.button("Delete this year", key=f"{key_prefix}_btn_del_year"):
                    if confirm_year:
                        df = df[df["Year"] != year_choice]
                        save_data(df, data_file)
                        st.session_state.pop(f"{key_prefix}_del_year", None)
                        st.session_state.pop(f"{key_prefix}_confirm_year", None)
                        st.success(f"Deleted all data for {year_choice}.")
                        st.rerun()
                    else:
                        st.warning("Please check the confirmation box first.")
        else:
            st.write("No data to delete.")

    # ---------------- All-time data + export ----------------
    with st.expander("View all saved data / export"):
        if not df.empty:
            full_display = df.copy()
            for col in ["Income"] + CATEGORIES:
                full_display[col] = full_display[col].apply(lambda v: fmt(symbol, v))
            st.dataframe(full_display, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download all data as CSV", csv,
                                os.path.basename(data_file), "text/csv",
                                key=f"{key_prefix}_download")
        else:
            st.write("No data saved yet.")


st.title("Monthly Budget Allocator")
st.caption("Divide your monthly income across categories, tracked every month, every year.")

tab_naira, tab_dollar = st.tabs(["🇳🇬 Naira Savings", "💵 Dollar Savings"])

with tab_naira:
    render_section("Naira", "₦", "budget_data_naira.csv", "ngn")

with tab_dollar:
    render_section("Dollar", "$", "budget_data_dollar.csv", "usd")
          
