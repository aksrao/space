
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="OrbitGuard | Telemetry Health Monitor",
    page_icon="🛰️",
    layout="wide",
)

DATA_DIR = Path("data/processed")
TIME_COLUMN = "RecordingTime"

APID_FILES = {
    "APID_1": DATA_DIR / "APID_1_clean.csv",
    "APID_2": DATA_DIR / "APID_2_clean.csv",
    "APID_4": DATA_DIR / "APID_4_clean.csv",
    "APID_40": DATA_DIR / "APID_40_clean.csv",
    "APID_41": DATA_DIR / "APID_41_clean.csv",
}


@st.cache_data
def load_apid_data(file_path: str, apid: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)

    if TIME_COLUMN not in df.columns:
        raise ValueError(f"{apid} is missing {TIME_COLUMN}")

    df[TIME_COLUMN] = pd.to_datetime(df[TIME_COLUMN], errors="coerce")
    df = df.dropna(subset=[TIME_COLUMN]).sort_values(TIME_COLUMN)
    df = df.reset_index(drop=True)

    for column in df.columns:
        if column != TIME_COLUMN:
            df[column] = pd.to_numeric(df[column], errors="ignore")

    df["APID"] = apid
    return df


@st.cache_data
def load_all_apids(file_map: dict) -> pd.DataFrame:
    frames = []

    for apid, path in file_map.items():
        if path.exists():
            frames.append(load_apid_data(str(path), apid))

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True, sort=False)


def numeric_columns(df: pd.DataFrame) -> list[str]:
    excluded = {TIME_COLUMN}
    return [
        c for c in df.select_dtypes(include="number").columns
        if c not in excluded
    ]


def find_columns(df: pd.DataFrame, keywords: list[str]) -> list[str]:
    return [
        c for c in numeric_columns(df)
        if any(k in c.lower() for k in keywords)
    ]


def plot_signals(
    df: pd.DataFrame,
    columns: list[str],
    title: str,
    color_by_apid: bool = False,
):
    if not columns:
        st.info("No matching numeric signals available in this view.")
        return

    id_columns = [TIME_COLUMN]
    if color_by_apid and "APID" in df.columns:
        id_columns.append("APID")

    plot_df = df[id_columns + columns].melt(
        id_vars=id_columns,
        var_name="Signal",
        value_name="Value",
    ).dropna(subset=["Value"])

    if plot_df.empty:
        st.info("No values available for the selected signals.")
        return

    if color_by_apid:
        fig = px.line(
            plot_df,
            x=TIME_COLUMN,
            y="Value",
            color="APID",
            line_dash="Signal",
            title=title,
        )
    else:
        fig = px.line(
            plot_df,
            x=TIME_COLUMN,
            y="Value",
            color="Signal",
            title=title,
        )

    fig.update_layout(
        xaxis_title="Recording time",
        yaxis_title="Telemetry value (unit to be verified)",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_apid_dashboard(df: pd.DataFrame, apid_label: str):
    signals = numeric_columns(df)

    c1, c2, c3 = st.columns(3)
    c1.metric("Records", f"{len(df):,}")
    c2.metric("Numeric signals", len(signals))
    c3.metric("Missing cells", f"{df.isna().sum().sum():,}")

    power = find_columns(
        df,
        ["battery", "solar", "charger", "bus", "voltage", "current", "power"],
    )
    thermal = find_columns(df, ["temperature", "temp", "therm"])
    adcs = find_columns(
        df,
        ["gyro", "magnet", "sun sensor", "wheel", "attitude", "quaternion"],
    )
    comms = find_columns(
        df,
        ["trx", "transceiver", "receiver", "transmitter", "radio", "rssi"],
    )

    used = set(power + thermal + adcs + comms)
    other = [c for c in signals if c not in used]

    tabs = st.tabs(
        ["Overview", "Power", "Thermal", "ADCS", "Communications", "Other", "Data Quality"]
    )

    with tabs[0]:
        st.dataframe(
            pd.DataFrame({
                "Signal": signals,
                "Missing (%)": [
                    round(df[c].isna().mean() * 100, 2) for c in signals
                ],
                "Unique values": [df[c].nunique(dropna=True) for c in signals],
            }),
            use_container_width=True,
            hide_index=True,
        )
        st.dataframe(df.head(15), use_container_width=True, hide_index=True)

    with tabs[1]:
        selected = st.multiselect(
            "Power signals",
            power,
            default=power[: min(6, len(power))],
            key=f"{apid_label}_power",
        )
        plot_signals(df, selected, f"{apid_label} — Power")

    with tabs[2]:
        selected = st.multiselect(
            "Thermal signals",
            thermal,
            default=thermal[: min(6, len(thermal))],
            key=f"{apid_label}_thermal",
        )
        plot_signals(df, selected, f"{apid_label} — Thermal")

    with tabs[3]:
        selected = st.multiselect(
            "ADCS signals",
            adcs,
            default=adcs[: min(6, len(adcs))],
            key=f"{apid_label}_adcs",
        )
        plot_signals(df, selected, f"{apid_label} — ADCS")

    with tabs[4]:
        selected = st.multiselect(
            "Communications signals",
            comms,
            default=comms[: min(6, len(comms))],
            key=f"{apid_label}_comms",
        )
        plot_signals(df, selected, f"{apid_label} — Communications")

    with tabs[5]:
        selected = st.multiselect(
            "Other numeric signals",
            other,
            default=other[: min(6, len(other))],
            key=f"{apid_label}_other",
        )
        plot_signals(df, selected, f"{apid_label} — Other signals")

    with tabs[6]:
        missing = (
            df.isna().mean().mul(100).round(2)
            .rename("Missing (%)").reset_index()
            .rename(columns={"index": "Column"})
            .sort_values("Missing (%)", ascending=False)
        )
        st.dataframe(missing, use_container_width=True, hide_index=True)

        intervals = df[TIME_COLUMN].sort_values().diff().dropna()
        if not intervals.empty:
            q1, q2, q3 = st.columns(3)
            q1.metric("Median sample interval", str(intervals.median()))
            q2.metric("Maximum time gap", str(intervals.max()))
            q3.metric(
                "Duplicate timestamps",
                int(df[TIME_COLUMN].duplicated().sum()),
            )


# -----------------------------
# Load files and choose view
# -----------------------------
available_files = {
    apid: path for apid, path in APID_FILES.items() if path.exists()
}

if not available_files:
    st.error("No cleaned APID files found under data/processed/.")
    st.stop()

st.sidebar.title("OrbitGuard")
view_mode = st.sidebar.radio(
    "Dashboard View",
    ["All APIDs", "Individual APID"],
)

all_df = load_all_apids(available_files)

st.title("🛰️ OrbitGuard")
st.caption(
    "Exploratory CubeSat telemetry monitoring. Signal units and operational "
    "limits must be verified against mission documentation before alerts are defined."
)

if view_mode == "All APIDs":
    st.subheader("Combined telemetry dashboard — all available APIDs")

    if all_df.empty:
        st.error("Could not load telemetry data.")
        st.stop()

    min_time = all_df[TIME_COLUMN].min().to_pydatetime()
    max_time = all_df[TIME_COLUMN].max().to_pydatetime()

    if min_time < max_time:
        time_range = st.sidebar.slider(
            "Time range",
            min_value=min_time,
            max_value=max_time,
            value=(min_time, max_time),
            format="YYYY-MM-DD HH:mm:ss",
            key="all_apid_time",
        )
        view_df = all_df[
            all_df[TIME_COLUMN].between(
                pd.Timestamp(time_range[0]),
                pd.Timestamp(time_range[1]),
            )
        ].copy()
    else:
        view_df = all_df.copy()

    a, b, c = st.columns(3)
    a.metric("Total records", f"{len(view_df):,}")
    b.metric("APIDs loaded", view_df["APID"].nunique())
    c.metric("Numeric signals", len(numeric_columns(view_df)))

    st.markdown("### Records by APID")
    counts = view_df.groupby("APID").size().reset_index(name="Records")
    st.bar_chart(counts, x="APID", y="Records")

    st.markdown("### Combined signal explorer")
    available_signals = numeric_columns(view_df)

    selected_signals = st.multiselect(
        "Choose signals to plot",
        available_signals,
        default=available_signals[: min(5, len(available_signals))],
        key="combined_signals",
    )

    plot_signals(
        view_df,
        selected_signals,
        "Telemetry across APIDs",
        color_by_apid=True,
    )

    st.markdown("### File-wise summaries")
    for apid in available_files:
        apid_df = view_df[view_df["APID"] == apid]
        with st.expander(f"{apid} — {len(apid_df):,} records"):
            render_apid_dashboard(apid_df, f"combined_{apid}")

else:
    selected_apid = st.sidebar.selectbox(
        "Select APID",
        list(available_files.keys()),
    )

    apid_df = all_df[all_df["APID"] == selected_apid].copy()

    if apid_df.empty:
        st.warning(f"No data available for {selected_apid}.")
        st.stop()

    min_time = apid_df[TIME_COLUMN].min().to_pydatetime()
    max_time = apid_df[TIME_COLUMN].max().to_pydatetime()

    if min_time < max_time:
        time_range = st.sidebar.slider(
            "Time range",
            min_value=min_time,
            max_value=max_time,
            value=(min_time, max_time),
            format="YYYY-MM-DD HH:mm:ss",
            key=f"{selected_apid}_time",
        )
        apid_df = apid_df[
            apid_df[TIME_COLUMN].between(
                pd.Timestamp(time_range[0]),
                pd.Timestamp(time_range[1]),
            )
        ].copy()

    st.subheader(f"Individual telemetry dashboard — {selected_apid}")
    render_apid_dashboard(apid_df, selected_apid)
