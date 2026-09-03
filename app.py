"""
Interactive Sales Dashboard - Streamlit
Rebuilt to mirror the original Power BI report: Overview, Rep Performance,
Product Category, Segment & Geography, Map, and Insights.
Run locally with: streamlit run app.py
Deploy free at: https://share.streamlit.io
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Sales Dashboard", page_icon="📊", layout="wide")

# ---------- LOAD DATA ----------
@st.cache_data
def load_data():
    df = pd.read_csv("sales_data.csv", parse_dates=["Order_Date", "Ship_Date"])
    targets = pd.read_csv("targets_data.csv", parse_dates=["Month_Start"])
    return df, targets

df, targets = load_data()

# ---------- SIDEBAR FILTERS (apply across all tabs) ----------
st.sidebar.header("Filters")

start_date = st.sidebar.date_input("Start date", df["Order_Date"].min(),
                                    min_value=df["Order_Date"].min(), max_value=df["Order_Date"].max())
end_date = st.sidebar.date_input("End date", df["Order_Date"].max(),
                                  min_value=df["Order_Date"].min(), max_value=df["Order_Date"].max())
if start_date > end_date:
    st.sidebar.error("Start date must be before end date.")
    st.stop()

regions = st.sidebar.multiselect("Region", sorted(df["Customer_Region"].dropna().unique()),
                                  default=sorted(df["Customer_Region"].dropna().unique()))
segments = st.sidebar.multiselect("Segment", sorted(df["Segment"].dropna().unique()),
                                   default=sorted(df["Segment"].dropna().unique()))
categories = st.sidebar.multiselect("Product Category", sorted(df["Product_Category"].dropna().unique()),
                                     default=sorted(df["Product_Category"].dropna().unique()))
channels = st.sidebar.multiselect("Channel", sorted(df["Channel"].dropna().unique()),
                                   default=sorted(df["Channel"].dropna().unique()))

mask = (
    (df["Order_Date"] >= pd.to_datetime(start_date)) & (df["Order_Date"] <= pd.to_datetime(end_date))
    & (df["Customer_Region"].isin(regions)) & (df["Segment"].isin(segments))
    & (df["Product_Category"].isin(categories)) & (df["Channel"].isin(channels))
)
f = df[mask].copy()

t_mask = (
    (targets["Month_Start"] >= pd.to_datetime(start_date)) & (targets["Month_Start"] <= pd.to_datetime(end_date))
    & (targets["Region"].isin(regions))
)
ft = targets[t_mask].copy()

st.title("📊 Sales Performance Dashboard")
st.caption("Interactive rebuild of the Power BI report — Python + Streamlit")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["Sales Overview", "Rep Performance", "Product Category", "Segment & Geography", "Map", "Key Insights"]
)

# ================= TAB 1: SALES OVERVIEW =================
with tab1:
    net_sales = f["Net_Sales_INR"].sum()
    gross_profit = f["Gross_Profit_INR"].sum()
    gross_margin = f["Gross_Profit_INR"].sum() / net_sales if net_sales else 0
    units = f["Units"].sum()
    return_rate = (f["Returned_Flag"] == "Yes").mean() if len(f) else 0
    otd = (f["On_Time_Delivery_Flag"] == "Yes").mean() if len(f) else 0
    target_total = ft["Monthly_Sales_Target_INR"].sum()
    attainment = net_sales / target_total if target_total else 0

    # Prior-year net sales, for the PY comparison card (mirrors "Net Sales PY" in the PBI report)
    py_start = pd.to_datetime(start_date) - pd.DateOffset(years=1)
    py_end = pd.to_datetime(end_date) - pd.DateOffset(years=1)
    py_mask = (df["Order_Date"] >= py_start) & (df["Order_Date"] <= py_end) & (df["Customer_Region"].isin(regions))
    net_sales_py = df[py_mask]["Net_Sales_INR"].sum()
    yoy_delta = (net_sales - net_sales_py) / net_sales_py if net_sales_py else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Net Sales", f"₹{net_sales/1e9:.2f}bn", delta=f"{yoy_delta:+.1%} YoY")
    c2.metric("Gross Profit", f"₹{gross_profit/1e9:.2f}bn")
    c3.metric("Gross Margin %", f"{gross_margin:.1%}",
              delta=f"{(gross_margin-0.45):+.1%} vs 45% target")
    c4.metric("Units", f"{units/1000:.0f}K")

    c5, c6, c7, c8 = st.columns(4)
    # Return rate: lower is better, so invert delta_color logic
    c5.metric("Return Rate", f"{return_rate:.1%}",
              delta=f"{(return_rate-0.05):+.1%} vs 5% target", delta_color="inverse")
    c6.metric("On-Time Delivery", f"{otd:.1%}",
              delta=f"{(otd-0.90):+.1%} vs 90% target")
    c7.metric("Target Attainment %", f"{attainment:.0%}",
              delta=f"{(attainment-1):+.0%} vs 100%")
    status = "Below Target" if attainment < 1 else "On Target"
    status_color = "#d62728" if attainment < 1 else "#2ca02c"
    c8.markdown("**Attainment Status**")
    c8.markdown(f"<span style='color:{status_color}; font-size:1.6rem; font-weight:600'>{status}</span>",
                unsafe_allow_html=True)

    st.divider()

    monthly = f.groupby(f["Order_Date"].dt.to_period("M"))["Net_Sales_INR"].sum().reset_index()
    monthly["Order_Date"] = monthly["Order_Date"].dt.to_timestamp()
    monthly_target = ft.groupby(ft["Month_Start"].dt.to_period("M"))["Monthly_Sales_Target_INR"].sum().reset_index()
    monthly_target["Month_Start"] = monthly_target["Month_Start"].dt.to_timestamp()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly["Order_Date"], y=monthly["Net_Sales_INR"],
                              mode="lines+markers", name="Net Sales", line=dict(color="#1f77b4")))
    fig.add_trace(go.Scatter(x=monthly_target["Month_Start"], y=monthly_target["Monthly_Sales_Target_INR"],
                              mode="lines", name="Sales Target", line=dict(color="orange", dash="dash")))
    fig.update_layout(title="Net Sales vs Sales Target (Monthly)", yaxis_title="INR")
    st.plotly_chart(fig, width="stretch")

    # Year-over-year monthly comparison (mirrors the small 2024 vs 2025 chart in the PBI overview)
    yoy = f.copy()
    yoy["Year"] = yoy["Order_Date"].dt.year.astype(str)
    yoy["Month"] = yoy["Order_Date"].dt.month
    yoy_grouped = yoy.groupby(["Year", "Month"])["Net_Sales_INR"].sum().reset_index()
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    yoy_grouped["Month_Name"] = yoy_grouped["Month"].apply(lambda m: month_names[m - 1])

    fig_yoy = px.line(
        yoy_grouped, x="Month_Name", y="Net_Sales_INR", color="Year", markers=True,
        category_orders={"Month_Name": month_names, "Year": sorted(yoy_grouped["Year"].unique())},
        title="Year-over-Year Net Sales Comparison",
        color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
    )
    fig_yoy.update_layout(yaxis_title="Net Sales (INR)", xaxis_title="")
    st.plotly_chart(fig_yoy, width="stretch")

    region_rev = f.groupby("Customer_Region")["Net_Sales_INR"].sum().reset_index()
    fig_region = px.bar(region_rev.sort_values("Net_Sales_INR"), x="Net_Sales_INR", y="Customer_Region",
                         orientation="h", title="Net Sales by Region")
    st.plotly_chart(fig_region, width="stretch")

# ================= TAB 2: REP PERFORMANCE =================
with tab2:
    rep_summary = f.groupby("Sales_Rep").agg(
        Net_Sales=("Net_Sales_INR", "sum"),
        Gross_Profit=("Gross_Profit_INR", "sum"),
        Avg_Discount=("Discount_Pct", "mean"),
        Return_Rate=("Returned_Flag", lambda x: (x == "Yes").mean()),
        Region=("Customer_Region", "first"),
        Tenure=("Rep_Tenure", "first"),
    ).reset_index()
    rep_summary["Gross_Margin_Pct"] = rep_summary["Gross_Profit"] / rep_summary["Net_Sales"]

    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("Gross Margin %", f"{rep_summary['Gross_Profit'].sum()/rep_summary['Net_Sales'].sum():.1%}")
    rc2.metric("Avg Discount %", f"{rep_summary['Avg_Discount'].mean():.2%}")
    rc3.metric("Reps", f"{f['Sales_Rep'].nunique()}")

    st.divider()

    q1, q2 = st.columns((2, 1))
    with q1:
        x_mid = rep_summary["Avg_Discount"].mean()
        y_mid = rep_summary["Gross_Margin_Pct"].mean()
        x_min, x_max = rep_summary["Avg_Discount"].min() * 0.9, rep_summary["Avg_Discount"].max() * 1.05
        y_min, y_max = rep_summary["Gross_Margin_Pct"].min() * 0.9, rep_summary["Gross_Margin_Pct"].max() * 1.05

        fig_quad = px.scatter(
            rep_summary, x="Avg_Discount", y="Gross_Margin_Pct", color="Region",
            hover_name="Sales_Rep", title="Gross Margin % vs Avg Discount % (by Rep)",
            labels={"Avg_Discount": "Avg Discount %", "Gross_Margin_Pct": "Gross Margin %"},
        )
        # Conditional-formatting-style shaded quadrant backgrounds, matching the PBI layout
        fig_quad.add_shape(type="rect", x0=x_min, x1=x_mid, y0=y_mid, y1=y_max,
                            fillcolor="#2ca02c", opacity=0.08, line_width=0, layer="below")
        fig_quad.add_shape(type="rect", x0=x_mid, x1=x_max, y0=y_mid, y1=y_max,
                            fillcolor="#1f77b4", opacity=0.08, line_width=0, layer="below")
        fig_quad.add_shape(type="rect", x0=x_min, x1=x_mid, y0=y_min, y1=y_mid,
                            fillcolor="#7f7f7f", opacity=0.08, line_width=0, layer="below")
        fig_quad.add_shape(type="rect", x0=x_mid, x1=x_max, y0=y_min, y1=y_mid,
                            fillcolor="#d62728", opacity=0.10, line_width=0, layer="below")
        fig_quad.add_annotation(x=x_min, y=y_max, text="Top Performers", showarrow=False,
                                 xanchor="left", yanchor="top", font=dict(color="#2ca02c", size=12))
        fig_quad.add_annotation(x=x_max, y=y_max, text="Volume Drivers", showarrow=False,
                                 xanchor="right", yanchor="top", font=dict(color="#1f77b4", size=12))
        fig_quad.add_annotation(x=x_min, y=y_min, text="Maintain", showarrow=False,
                                 xanchor="left", yanchor="bottom", font=dict(color="#7f7f7f", size=12))
        fig_quad.add_annotation(x=x_max, y=y_min, text="High Risk", showarrow=False,
                                 xanchor="right", yanchor="bottom", font=dict(color="#d62728", size=12))
        fig_quad.add_hline(y=y_mid, line_dash="dot", line_color="gray")
        fig_quad.add_vline(x=x_mid, line_dash="dot", line_color="gray")
        fig_quad.update_layout(xaxis_tickformat=".1%", yaxis_tickformat=".0%",
                                xaxis_range=[x_min, x_max], yaxis_range=[y_min, y_max])
        st.plotly_chart(fig_quad, width="stretch")

    with q2:
        tenure_order = ["<1 year", "1-2 years", "2-4 years", "4+ years"]
        tenure_margin = rep_summary.groupby("Tenure")["Gross_Margin_Pct"].mean().reindex(tenure_order).reset_index()
        fig_tenure = px.line(tenure_margin, x="Tenure", y="Gross_Margin_Pct", markers=True,
                              title="Gross Margin % by Rep Tenure")
        fig_tenure.update_layout(yaxis_tickformat=".1%")
        st.plotly_chart(fig_tenure, width="stretch")

    st.subheader("Top 10 Reps by Net Sales")
    top10 = rep_summary.sort_values("Net_Sales", ascending=False).head(10).copy()
    top10 = top10[["Sales_Rep", "Region", "Net_Sales", "Gross_Margin_Pct", "Return_Rate"]]

    styled_top10 = (
        top10.style
        .background_gradient(subset=["Net_Sales"], cmap="Greens")
        .background_gradient(subset=["Gross_Margin_Pct"], cmap="Greens")
        .background_gradient(subset=["Return_Rate"], cmap="Reds")
        .format({"Net_Sales": "₹{:,.0f}", "Gross_Margin_Pct": "{:.1%}", "Return_Rate": "{:.1%}"})
    )
    st.dataframe(styled_top10, width="stretch", hide_index=True)

# ================= TAB 3: PRODUCT CATEGORY =================
with tab3:
    cat_summary = f.groupby("Product_Category").agg(
        Net_Sales=("Net_Sales_INR", "sum"),
        Gross_Profit=("Gross_Profit_INR", "sum"),
        Return_Rate=("Returned_Flag", lambda x: (x == "Yes").mean()),
        Units=("Units", "sum"),
        Avg_Discount=("Discount_Pct", "mean"),
    ).reset_index()
    cat_summary["Gross_Margin_Pct"] = cat_summary["Gross_Profit"] / cat_summary["Net_Sales"]

    pc1, pc2, pc3 = st.columns(3)
    pc1.metric("Total Products", f"{f['Product'].nunique()}")
    pc2.metric("Product Subcategories", f"{f['Product_Subcategory'].nunique()}")
    pc3.metric("Product Categories", f"{f['Product_Category'].nunique()}")

    fig_cat = go.Figure()
    fig_cat.add_trace(go.Bar(x=cat_summary["Product_Category"], y=cat_summary["Net_Sales"], name="Net Sales"))
    fig_cat.add_trace(go.Scatter(x=cat_summary["Product_Category"], y=cat_summary["Gross_Margin_Pct"],
                                  name="Gross Margin %", yaxis="y2", mode="lines+markers", line=dict(color="orange")))
    fig_cat.update_layout(
        title="Net Sales & Gross Margin % by Product Category",
        yaxis=dict(title="Net Sales (INR)"),
        yaxis2=dict(title="Gross Margin %", overlaying="y", side="right", tickformat=".0%"),
    )
    st.plotly_chart(fig_cat, width="stretch")

    st.subheader("Gross Margin % Heat Map — Subcategory × Region")
    heat_data = f.groupby(["Product_Subcategory", "Customer_Region"]).apply(
        lambda x: x["Gross_Profit_INR"].sum() / x["Net_Sales_INR"].sum() if x["Net_Sales_INR"].sum() else 0
    ).reset_index(name="Gross_Margin_Pct")
    heat_pivot = heat_data.pivot(index="Product_Subcategory", columns="Customer_Region", values="Gross_Margin_Pct")

    fig_heat = px.imshow(
        heat_pivot, text_auto=".1%", color_continuous_scale="RdYlGn",
        aspect="auto", title="Gross Margin % by Product Subcategory and Region",
        labels=dict(color="Gross Margin %"),
    )
    fig_heat.update_layout(coloraxis_colorbar_tickformat=".0%")
    st.plotly_chart(fig_heat, width="stretch")

    tbl = cat_summary.copy()
    styled_tbl = (
        tbl.style
        .background_gradient(subset=["Net_Sales"], cmap="Blues")
        .background_gradient(subset=["Gross_Margin_Pct"], cmap="Greens")
        .background_gradient(subset=["Return_Rate"], cmap="Reds")
        .format({
            "Net_Sales": "₹{:,.0f}", "Gross_Profit": "₹{:,.0f}",
            "Gross_Margin_Pct": "{:.1%}", "Return_Rate": "{:.1%}",
            "Avg_Discount": "{:.2%}", "Units": "{:,.0f}",
        })
    )
    st.dataframe(styled_tbl, width="stretch", hide_index=True)

# ================= TAB 4: SEGMENT & GEOGRAPHY =================
with tab4:
    g1, g2 = st.columns(2)
    with g1:
        seg_rev = f.groupby("Segment")["Net_Sales_INR"].sum().reset_index()
        fig_seg = px.pie(seg_rev, names="Segment", values="Net_Sales_INR", hole=0.4, title="Net Sales by Segment")
        st.plotly_chart(fig_seg, width="stretch")

    with g2:
        otd_channel = f.groupby("Channel").apply(lambda x: (x["On_Time_Delivery_Flag"] == "Yes").mean()).reset_index(name="OTD")
        otd_channel = otd_channel.sort_values("OTD", ascending=False)
        # Conditional formatting: green if OTD >= 85%, amber 75-85%, red below 75%
        otd_channel["Status"] = otd_channel["OTD"].apply(
            lambda v: "On Target" if v >= 0.85 else ("Watch" if v >= 0.75 else "At Risk"))
        color_map = {"On Target": "#2ca02c", "Watch": "#ff7f0e", "At Risk": "#d62728"}
        fig_otd = px.bar(otd_channel, x="Channel", y="OTD", color="Status", color_discrete_map=color_map,
                          title="On-Time Delivery % by Channel")
        fig_otd.add_hline(y=0.85, line_dash="dot", line_color="gray", annotation_text="85% target")
        fig_otd.update_layout(yaxis_tickformat=".0%")
        st.plotly_chart(fig_otd, width="stretch")

    g3, g4 = st.columns(2)
    with g3:
        nps_seg = f.groupby("Segment")["NPS_Score"].mean().reset_index()
        fig_nps = px.bar(nps_seg, x="Segment", y="NPS_Score", title="Avg NPS by Segment")
        st.plotly_chart(fig_nps, width="stretch")

    with g4:
        ind_rev = f.groupby("Industry")["Net_Sales_INR"].sum().reset_index().sort_values("Net_Sales_INR")
        fig_ind = px.bar(ind_rev, x="Net_Sales_INR", y="Industry", orientation="h", title="Net Sales by Industry")
        st.plotly_chart(fig_ind, width="stretch")

    st.subheader("Top 20 Customers by Net Sales")
    top_cust = f.groupby("Customer_Name")["Net_Sales_INR"].sum().reset_index().sort_values(
        "Net_Sales_INR", ascending=False).head(20)
    styled_cust = (
        top_cust.style
        .background_gradient(subset=["Net_Sales_INR"], cmap="Greens")
        .format({"Net_Sales_INR": "₹{:,.0f}"})
    )
    st.dataframe(styled_cust, width="stretch", hide_index=True)

# ================= TAB 5: MAP =================
with tab5:
    city_rev = f.dropna(subset=["Lat", "Lon"]).groupby(["City", "Lat", "Lon"])["Net_Sales_INR"].sum().reset_index()
    fig_map = px.scatter_geo(
        city_rev, lat="Lat", lon="Lon", size="Net_Sales_INR", hover_name="City",
        scope="asia", title="Net Sales by City",
        size_max=40,
    )
    fig_map.update_geos(center=dict(lat=22, lon=80), projection_scale=4, showcountries=True)
    st.plotly_chart(fig_map, width="stretch")

# ================= TAB 6: KEY INSIGHTS =================
with tab6:
    st.caption("Auto-generated from the current filter selection — change filters on the left and these update.")

    insights = []

    if len(f) == 0:
        st.warning("No data matches the current filters. Adjust filters to see insights.")
    else:
        # --- Seasonality: peak vs trough month ---
        month_rev = f.groupby(f["Order_Date"].dt.month)["Net_Sales_INR"].sum()
        if len(month_rev) >= 2:
            month_names_full = ["January","February","March","April","May","June","July",
                                 "August","September","October","November","December"]
            peak_month = month_rev.idxmax()
            trough_month = month_rev.idxmin()
            peak_val, trough_val = month_rev.max(), month_rev.min()
            drop_pct = (peak_val - trough_val) / peak_val if peak_val else 0
            insights.append(
                f"**Seasonality:** {month_names_full[peak_month-1]} is the strongest month "
                f"(₹{peak_val/1e6:,.0f}M) and {month_names_full[trough_month-1]} the weakest "
                f"(₹{trough_val/1e6:,.0f}M) — a {drop_pct:.0%} swing between the two, "
                f"worth factoring into inventory and staffing plans."
            )

        # --- Region: revenue gap vs margin gap ---
        region_stats = f.groupby("Customer_Region").agg(
            Net_Sales=("Net_Sales_INR", "sum"), Gross_Profit=("Gross_Profit_INR", "sum")
        )
        if len(region_stats) >= 2:
            region_stats["Margin"] = region_stats["Gross_Profit"] / region_stats["Net_Sales"]
            top_region = region_stats["Net_Sales"].idxmax()
            low_region = region_stats["Net_Sales"].idxmin()
            rev_gap = 1 - (region_stats.loc[low_region, "Net_Sales"] / region_stats.loc[top_region, "Net_Sales"])
            margin_gap = region_stats["Margin"].max() - region_stats["Margin"].min()
            insights.append(
                f"**Regional gap:** {low_region} trails {top_region} by {rev_gap:.0%} on revenue, "
                f"but the margin spread across regions is only {margin_gap:.1%} — "
                f"the gap looks like a demand/coverage issue rather than a pricing or execution issue."
            )

        # --- Discount vs margin quadrant ---
        rep_stats = f.groupby("Sales_Rep").agg(
            Net_Sales=("Net_Sales_INR", "sum"), Gross_Profit=("Gross_Profit_INR", "sum"),
            Avg_Discount=("Discount_Pct", "mean"),
        )
        if len(rep_stats) >= 2:
            rep_stats["Margin"] = rep_stats["Gross_Profit"] / rep_stats["Net_Sales"]
            disc_mid, margin_mid = rep_stats["Avg_Discount"].mean(), rep_stats["Margin"].mean()
            high_risk = rep_stats[(rep_stats["Avg_Discount"] > disc_mid) & (rep_stats["Margin"] < margin_mid)]
            pct_high_risk = len(high_risk) / len(rep_stats)
            insights.append(
                f"**Discounting:** {len(high_risk)} of {len(rep_stats)} reps ({pct_high_risk:.0%}) sit in the "
                f"'High Risk' quadrant — above-average discounting paired with below-average margin. "
                f"The rest of the team holds healthy margins regardless of discount level, "
                f"so this looks concentrated rather than systemic."
            )

        # --- Product category: revenue share vs margin ---
        cat_stats = f.groupby("Product_Category").agg(
            Net_Sales=("Net_Sales_INR", "sum"), Gross_Profit=("Gross_Profit_INR", "sum"),
            Returned=("Returned_Flag", lambda x: (x == "Yes").mean()),
        )
        if len(cat_stats) >= 2:
            cat_stats["Margin"] = cat_stats["Gross_Profit"] / cat_stats["Net_Sales"]
            cat_stats["Rev_Share"] = cat_stats["Net_Sales"] / cat_stats["Net_Sales"].sum()
            top_rev_cat = cat_stats["Rev_Share"].idxmax()
            top_margin_cat = cat_stats["Margin"].idxmax()
            insights.append(
                f"**Product mix:** {top_rev_cat} drives the largest share of revenue "
                f"({cat_stats.loc[top_rev_cat,'Rev_Share']:.0%}) but runs a "
                f"{cat_stats.loc[top_rev_cat,'Margin']:.0%} margin and a "
                f"{cat_stats.loc[top_rev_cat,'Returned']:.1%} return rate, while {top_margin_cat} "
                f"carries the highest margin at {cat_stats.loc[top_margin_cat,'Margin']:.0%}."
            )

        # --- Segment leader ---
        seg_stats = f.groupby("Segment").agg(
            Net_Sales=("Net_Sales_INR", "sum"), Gross_Profit=("Gross_Profit_INR", "sum")
        )
        if len(seg_stats) >= 2:
            seg_stats["Margin"] = seg_stats["Gross_Profit"] / seg_stats["Net_Sales"]
            top_seg_rev = seg_stats["Net_Sales"].idxmax()
            top_seg_margin = seg_stats["Margin"].idxmax()
            low_seg = seg_stats["Net_Sales"].idxmin()
            if top_seg_rev == top_seg_margin:
                insights.append(
                    f"**Segment:** {top_seg_rev} leads on both revenue and margin; "
                    f"{low_seg} lags on both dimensions."
                )
            else:
                insights.append(
                    f"**Segment:** {top_seg_rev} leads on revenue while {top_seg_margin} leads on margin; "
                    f"{low_seg} has the lowest revenue."
                )

        # --- Target attainment ---
        target_total = ft["Monthly_Sales_Target_INR"].sum()
        if target_total:
            attainment = f["Net_Sales_INR"].sum() / target_total
            status = "below target" if attainment < 1 else "at or above target"
            insights.append(f"**Target attainment:** Current selection is running at {attainment:.0%}, {status}.")

        for insight in insights:
            st.markdown(f"- {insight}")

    st.caption("Filters on the left apply across all tabs.")
