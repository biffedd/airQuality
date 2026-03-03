import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import random

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="NYC Air Quality Dashboard",
    page_icon="🌆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Load data ────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("Air_Quality.csv", encoding="utf-8-sig")
    df["Start_Date"] = pd.to_datetime(df["Start_Date"], errors="coerce")
    df["Year"] = df["Start_Date"].dt.year
    return df

df = load_data()

# ── Sidebar filters ──────────────────────────────────────────
st.sidebar.title("🔎 Filters")

pollutants = sorted(df["Name"].dropna().unique().tolist())
sel_pollutant = st.sidebar.selectbox("Pollutant", pollutants,
    index=pollutants.index("Nitrogen dioxide (NO2)") if "Nitrogen dioxide (NO2)" in pollutants else 0)

years = sorted(df["Year"].dropna().unique().astype(int).tolist())
yr_min, yr_max = st.sidebar.select_slider(
    "Year range",
    options=years,
    value=(min(years), max(years))
)

geo_types = df["Geo Type Name"].dropna().unique().tolist()
sel_geo = st.sidebar.multiselect("Geo Type", geo_types, default=["CD"])

top_n = st.sidebar.slider("Top N districts (charts)", 5, 40, 20)

# ── Filtered dataframe ───────────────────────────────────────
df_f = df[
    df["Name"].eq(sel_pollutant) &
    df["Year"].between(yr_min, yr_max) &
    df["Geo Type Name"].isin(sel_geo)
].copy()

df_agg = (
    df_f.groupby(["Geo Place Name"], as_index=False)["Data Value"]
    .mean()
    .rename(columns={"Data Value": "Mean Value"})
    .sort_values("Mean Value", ascending=False)
    .head(top_n)
)

# ── Coordinates lookup ───────────────────────────────────────
cd_coords = {
    "Financial District (CD1)": (40.7075, -74.0021),
    "Greenwich Village and Soho (CD2)": (40.7282, -74.0040),
    "Lower East Side and Chinatown (CD3)": (40.7157, -73.9863),
    "Clinton and Chelsea (CD4)": (40.7484, -74.0020),
    "Midtown (CD5)": (40.7549, -73.9840),
    "Stuyvesant Town and Turtle Bay (CD6)": (40.7420, -73.9758),
    "Upper West Side (CD7)": (40.7870, -73.9754),
    "Upper East Side (CD8)": (40.7736, -73.9566),
    "Morningside Heights and Hamilton Heights (CD9)": (40.8116, -73.9535),
    "Central Harlem (CD10)": (40.8116, -73.9465),
    "East Harlem (CD11)": (40.7957, -73.9389),
    "Washington Heights and Inwood (CD12)": (40.8448, -73.9393),
    "Williamsburg and Bushwick (CD4)": (40.7081, -73.9571),
    "Park Slope and Carroll Gardens (CD6)": (40.6736, -73.9776),
    "Fort Greene and Brooklyn Heights (CD2)": (40.6877, -73.9754),
    "Flatbush and Midwood (CD14)": (40.6296, -73.9559),
    "Flatlands and Canarsie (CD18)": (40.6359, -73.9199),
    "Flushing and Whitestone (CD7)": (40.7676, -73.8330),
    "Fordham and University Heights (CD5)": (40.8594, -73.9014),
    "Morrisania and Crotona (CD3)": (40.8367, -73.9092),
    "Highbridge and South Bronx (CD4)": (40.8160, -73.9237),
    "Elmhurst and Corona (CD4)": (40.7385, -73.8654),
    "Jackson Heights (CD3)": (40.7557, -73.8831),
    "Rockaway and Broad Channel (CD14)": (40.5855, -73.8272),
    "Stapleton and St. George (CD1)": (40.6370, -74.0776),
}
borough_fallback = {
    "Manhattan": (40.7831, -73.9712),
    "Brooklyn": (40.6782, -73.9442),
    "Queens": (40.7282, -73.7949),
    "Bronx": (40.8448, -73.8648),
    "Staten": (40.5795, -74.1502),
}

def get_coords(name):
    if name in cd_coords:
        return cd_coords[name]
    for b, c in borough_fallback.items():
        if b.lower() in name.lower():
            return (c[0] + random.uniform(-0.01, 0.01),
                    c[1] + random.uniform(-0.01, 0.01))
    return (40.7128 + random.uniform(-0.02, 0.02),
            -74.0060 + random.uniform(-0.02, 0.02))

df_agg[["lat", "lon"]] = pd.DataFrame(
    df_agg["Geo Place Name"].apply(get_coords).tolist(),
    columns=["lat", "lon"],
    index=df_agg.index
)

# ── Title ────────────────────────────────────────────────────
st.title("🌆 NYC Air Quality Dashboard")
st.markdown(f"Showing **{sel_pollutant}** · {yr_min}–{yr_max} · Top {top_n} districts")
st.divider()

# ── KPI metrics ──────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Districts shown", len(df_agg))
col2.metric("Max level", f"{df_agg['Mean Value'].max():.1f}" if len(df_agg) else "N/A")
col3.metric("Min level", f"{df_agg['Mean Value'].min():.1f}" if len(df_agg) else "N/A")
col4.metric("Avg level", f"{df_agg['Mean Value'].mean():.1f}" if len(df_agg) else "N/A")
st.divider()

# ── Chart 1: Zoomed NYC Map ───────────────────────────────────
st.subheader("📍 Geo Map – Zoomed into NYC (OpenStreetMap)")
if len(df_agg) > 0:
    fig_map = px.scatter_mapbox(
        df_agg,
        lat="lat", lon="lon",
        color="Mean Value",
        size="Mean Value",
        hover_name="Geo Place Name",
        hover_data={"Mean Value": ":.2f", "lat": False, "lon": False},
        color_continuous_scale="YlOrRd",
        size_max=35,
        zoom=10,
        center={"lat": 40.7300, "lon": -73.9350},
        mapbox_style="open-street-map",
        labels={"Mean Value": f"{sel_pollutant}"},
        height=520
    )
    fig_map.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_colorbar=dict(thickness=12)
    )
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("No data for selected filters.")

# ── Chart 2: Bar chart ───────────────────────────────────────
st.subheader("📊 Mean Pollutant Level by District")
if len(df_agg) > 0:
    fig_bar = px.bar(
        df_agg,
        x="Geo Place Name", y="Mean Value",
        color="Mean Value",
        color_continuous_scale="Reds",
        labels={"Geo Place Name": "District", "Mean Value": "Mean Level"},
        height=420
    )
    fig_bar.update_layout(
        xaxis_tickangle=-55,
        template="plotly_dark",
        margin=dict(b=160)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Chart 3 & 4 side-by-side ─────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("🌡️ Heatmap – All Pollutants × Districts")
    df_cd = df[df["Geo Type Name"] == "CD"].copy()
    df_all_agg = (
        df_cd.groupby(["Geo Place Name", "Name"], as_index=False)["Data Value"]
        .mean()
        .rename(columns={"Data Value": "Mean Value"})
    )
    top_dist = (
        df_all_agg.groupby("Geo Place Name")["Mean Value"].mean()
        .nlargest(12).index.tolist()
    )
    df_pivot = df_all_agg[df_all_agg["Geo Place Name"].isin(top_dist)].pivot_table(
        index="Geo Place Name", columns="Name", values="Mean Value", aggfunc="mean"
    )
    df_pivot.columns = [c.split("(")[0].strip() for c in df_pivot.columns]
    fig_hm, ax = plt.subplots(figsize=(9, 6))
    sns.heatmap(df_pivot, annot=True, fmt=".1f", cmap="YlOrRd",
                linewidths=0.4, ax=ax, cbar_kws={"shrink": 0.7})
    ax.set_xlabel("Pollutant", fontsize=9)
    ax.set_ylabel("District", fontsize=9)
    plt.xticks(rotation=35, ha="right", fontsize=7)
    plt.yticks(fontsize=7)
    plt.tight_layout()
    st.pyplot(fig_hm)

with right:
    st.subheader("📈 NO2 Trend Over Time – Top 6 Districts")
    df_trend_raw = df[
        (df["Name"] == "Nitrogen dioxide (NO2)") &
        (df["Geo Type Name"] == "CD")
    ].copy()
    df_trend_raw["Year"] = pd.to_datetime(df_trend_raw["Start_Date"], errors="coerce").dt.year
    top6 = (
        df_trend_raw.groupby("Geo Place Name")["Data Value"].mean()
        .nlargest(6).index.tolist()
    )
    df_trend = (
        df_trend_raw[df_trend_raw["Geo Place Name"].isin(top6)]
        .groupby(["Year", "Geo Place Name"], as_index=False)["Data Value"].mean()
    )
    fig_line = px.line(
        df_trend, x="Year", y="Data Value",
        color="Geo Place Name", markers=True,
        labels={"Data Value": "Mean NO2 (ppb)", "Geo Place Name": "District"},
        height=430
    )
    fig_line.update_layout(template="plotly_dark", hovermode="x unified",
                           legend=dict(font_size=9))
    st.plotly_chart(fig_line, use_container_width=True)

# ── Raw data table ───────────────────────────────────────────
with st.expander("📋 View raw filtered data"):
    st.dataframe(
        df_f[["Geo Place Name", "Name", "Time Period", "Data Value", "Year"]]
        .sort_values("Data Value", ascending=False)
        .reset_index(drop=True),
        use_container_width=True
    )

st.caption("Data source: NYC Open Data – Air Quality Survey")
