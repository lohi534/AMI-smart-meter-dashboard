import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime
import io

# --- Page Configuration ---
st.set_page_config(
    page_title="AMI Smart Meter Performance & SLA Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- High-Contrast Light Theme & Text Visibility Styling ---
st.markdown("""
<style>
    /* 1. Global Background & Dark Text */
    .stApp {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
    }
    
    /* 2. Text Visibility Enforcement */
    p, span, label, h1, h2, h3, h4, h5, h6, 
    div[data-testid="stMarkdownContainer"] *,
    .stWidgetLabel, .stRadio label {
        color: #0f172a !important;
        font-weight: 600 !important;
    }

    /* 3. Sidebar Clean Light Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 2px solid #cbd5e1 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #0f172a !important;
    }
    section[data-testid="stSidebar"] h3 {
        color: #0f172a !important;
        font-weight: 800 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzone"] {
        background-color: #f8fafc !important;
        border: 2px dashed #64748b !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzone"] * {
        color: #1e293b !important;
    }
    section[data-testid="stSidebar"] input {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #94a3b8 !important;
        font-weight: 700 !important;
    }

    /* 4. Canvas Radio Buttons */
    div[role="radiogroup"] label {
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    /* 5. Power BI KPI Cards */
    .pbi-card {
        background-color: #ffffff !important;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 14px;
        border: 1.5px solid #cbd5e1 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .pbi-card-blue { border-top: 5px solid #2563eb !important; }
    .pbi-card-green { border-top: 5px solid #10b981 !important; }
    .pbi-card-amber { border-top: 5px solid #f59e0b !important; }
    .pbi-card-purple { border-top: 5px solid #8b5cf6 !important; }

    .pbi-title {
        font-size: 0.8rem !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        color: #475569 !important;
        letter-spacing: 0.05em;
    }
    .pbi-val {
        font-size: 2.1rem !important;
        font-weight: 900 !important;
        color: #0f172a !important;
        margin: 6px 0;
    }
    
    /* 6. Badges */
    .badge-pass {
        color: #065f46 !important;
        background-color: #d1fae5 !important;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 800 !important;
        font-size: 0.78rem;
        display: inline-block;
    }
    .badge-fail {
        color: #991b1b !important;
        background-color: #fee2e2 !important;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 800 !important;
        font-size: 0.78rem;
        display: inline-block;
    }

    /* 7. Date Slicer Card */
    .slicer-card {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    /* 8. Top Banner */
    .banner-container {
        background-color: #ffffff !important;
        border-left: 6px solid #f59e0b !important;
        border: 1.5px solid #cbd5e1;
        border-radius: 6px;
        padding: 14px 20px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .banner-title {
        font-size: 1.4rem !important;
        font-weight: 900 !important;
        color: #0f172a !important;
        margin: 0;
    }
    .banner-sub {
        font-size: 0.86rem !important;
        color: #475569 !important;
        font-weight: 600 !important;
        margin-top: 3px;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Controls ---
st.sidebar.markdown("### ⚡ Ingestion Settings")
uploaded_file = st.sidebar.file_uploader("Upload AMI Excel / CSV", type=["xlsx", "xls", "csv"])

total_fleet_meters = st.sidebar.number_input(
    "Total Installed Fleet Baseline",
    min_value=1,
    value=1295000,
    step=1000
)

target_sla = st.sidebar.slider("Utility SLA Target (%)", 90.0, 100.0, 97.0, 0.2)

# --- Robust Automated ETL Engine ---
def run_ami_etl(file_upload):
    if file_upload:
        try:
            if file_upload.name.endswith(".csv"):
                # Try auto-detecting separator (comma, semicolon, tab)
                try:
                    raw = pd.read_csv(file_upload, sep=None, engine='python')
                except Exception:
                    file_upload.seek(0)
                    raw = pd.read_csv(file_upload)
            else:
                raw = pd.read_excel(file_upload)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()
    else:
        # Fallback simulated September 2026 dataset
        np.random.seed(42)
        dates = pd.date_range(start="2026-09-01", end="2026-09-30", freq="D")
        records = []
        for dt in dates:
            valid = int(np.random.normal(1265500, 1100))
            invalid = int(np.random.normal(3550, 160))
            no_comm = int(np.random.normal(3700, 280))
            billed = int(np.random.normal(1190000, 11000))
            records.append({
                "date": dt.strftime("%d-%m-%Y"),
                "communication_count_valid": valid,
                "communication_count_invaild": invalid,
                "no communication": no_comm,
                "Billed_reads": billed
            })
        raw = pd.DataFrame(records)

    df = raw.copy()
    
    # Clean and standardize column names
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w\s]", "", regex=True)
        .str.replace(" ", "_")
    )

    cols_list = list(df.columns)

    # 1. Date column mapping
    date_col = next((c for c in cols_list if any(k in c for k in ["date", "day", "time", "stamp"])), cols_list[0])

    # 2. Valid Communicating column mapping
    valid_col = next((c for c in cols_list if ("valid" in c and "invalid" not in c and "invaild" not in c) or "success" in c), None)

    # 3. Invalid Communicating column mapping
    invalid_col = next((c for c in cols_list if any(k in c for k in ["invalid", "invaild", "abnormal", "defect", "fail_read"])), None)

    # 4. No Communication column mapping
    no_comm_col = next((c for c in cols_list if any(k in c for k in ["no_comm", "not_comm", "failed", "offline", "unreach", "dropout"])), None)

    # 5. Billed Reads column mapping
    billed_col = next((c for c in cols_list if any(k in c for k in ["billed", "bill", "invoice"])), None)

    # --- Robust Index Fallbacks (if column headers differ from expectations) ---
    non_date_cols = [c for c in cols_list if c != date_col]
    if not valid_col and len(non_date_cols) > 0:
        valid_col = non_date_cols[0]
    if not invalid_col and len(non_date_cols) > 1:
        invalid_col = non_date_cols[1]
    if not no_comm_col and len(non_date_cols) > 2:
        no_comm_col = non_date_cols[2]
    if not billed_col and len(non_date_cols) > 3:
        billed_col = non_date_cols[3]

    # Convert Date safely
    df[date_col] = pd.to_datetime(df[date_col], format="%d-%m-%Y", errors="coerce")
    if df[date_col].isna().all():
        df[date_col] = pd.to_datetime(raw.iloc[:, 0], errors="coerce")
    
    # Fallback to date range if date parsing totally failed
    if df[date_col].isna().all():
        df[date_col] = pd.date_range(start="2026-09-01", periods=len(df), freq="D")

    # Clean numeric fields safely
    for c in [valid_col, invalid_col, no_comm_col, billed_col]:
        if c and c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Core Calculations
    df["received_meters"] = df[valid_col] + df[invalid_col]
    df["total_meters"] = total_fleet_meters
    df["comm_sla_pct"] = (df["received_meters"] / df["total_meters"]) * 100
    df["validity_pct"] = np.where(df["received_meters"] > 0, (df[valid_col] / df["received_meters"]) * 100, 0)
    df["billed_conv_pct"] = np.where(df["received_meters"] > 0, (df[billed_col] / df["received_meters"]) * 100, 0)
    df["billing_eff_pct"] = (df[billed_col] / df["total_meters"]) * 100
    
    df = df.sort_values(by=date_col)
    
    return df, {
        "date": date_col,
        "valid": valid_col,
        "invalid": invalid_col,
        "no_comm": no_comm_col,
        "billed": billed_col
    }

df, cols = run_ami_etl(uploaded_file)

# Top Banner
st.markdown(f"""
<div class="banner-container">
    <div class="banner-title">⚡ AMI Meter Fleet Communication & Billing SLA Command Center</div>
    <div class="banner-sub">Production Operations Dashboard | Active Base Cap: {total_fleet_meters:,} Nodes</div>
</div>
""", unsafe_allow_html=True)

# Date Slicer Bar
min_date_available = df[cols["date"]].min().date()
max_date_available = df[cols["date"]].max().date()

with st.container():
    st.markdown('<div class="slicer-card">', unsafe_allow_html=True)
    c_preset, c_slider, c_single = st.columns([2, 3, 2])
    
    with c_preset:
        date_mode = st.radio(
            "📅 Date Selection Mode",
            ["Full Month (30 Days)", "Last 14 Days", "Last 7 Days", "Custom Range"],
            horizontal=False
        )
        
    with c_slider:
        if date_mode == "Full Month (30 Days)":
            start_date, end_date = min_date_available, max_date_available
            st.info(f"Showing all records: **{start_date.strftime('%d-%b-%Y')}** to **{end_date.strftime('%d-%b-%Y')}**")
        elif date_mode == "Last 14 Days":
            end_date = max_date_available
            start_date = max(min_date_available, end_date - datetime.timedelta(days=13))
            st.info(f"Showing 14-day window: **{start_date.strftime('%d-%b-%Y')}** to **{end_date.strftime('%d-%b-%Y')}**")
        elif date_mode == "Last 7 Days":
            end_date = max_date_available
            start_date = max(min_date_available, end_date - datetime.timedelta(days=6))
            st.info(f"Showing 7-day window: **{start_date.strftime('%d-%b-%Y')}** to **{end_date.strftime('%d-%b-%Y')}**")
        else:
            date_range = st.date_input(
                "Pick Start & End Date",
                value=(min_date_available, max_date_available),
                min_value=min_date_available,
                max_value=max_date_available
            )
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date, end_date = min_date_available, max_date_available
            
    with c_single:
        cycle_count = (end_date - start_date).days + 1
        st.markdown(f"""
        <div style="text-align: center; padding: 10px;">
            <div style="font-size: 0.85rem; font-weight: 800; color: #475569;">ACTIVE CYCLE SCOPE</div>
            <div style="font-size: 2.1rem; font-weight: 900; color: #0f172a;">{cycle_count} Day(s)</div>
            <span class="badge-pass">{start_date.strftime('%d-%b')} → {end_date.strftime('%d-%b')}</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Apply Filter
filtered_df = df[
    (df[cols["date"]].dt.date >= start_date) & 
    (df[cols["date"]].dt.date <= end_date)
].copy()

if filtered_df.empty:
    st.warning("No records found for the selected date range. Reverting to full range.")
    filtered_df = df.copy()

latest = filtered_df.iloc[-1]
prev_day = filtered_df.iloc[-2] if len(filtered_df) > 1 else latest

# --- ROW 1: POWER BI MODULAR KPI TILES ---
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="pbi-card pbi-card-blue">
        <div class="pbi-title">Total Installed Fleet</div>
        <div class="pbi-val">{total_fleet_meters:,}</div>
        <span class="badge-pass" style="background:#e0f2fe; color:#0369a1 !important;">Active Grid Population</span>
    </div>
    """, unsafe_allow_html=True)

with k2:
    comm_pct = latest["comm_sla_pct"]
    comm_delta = comm_pct - prev_day["comm_sla_pct"]
    delta_symbol = "▲" if comm_delta >= 0 else "▼"
    badge_style = "badge-pass" if comm_pct >= target_sla else "badge-fail"
    st.markdown(f"""
    <div class="pbi-card pbi-card-green">
        <div class="pbi-title">Received Meters ({latest[cols['date']].strftime('%d-%b')})</div>
        <div class="pbi-val">{int(latest['received_meters']):,}</div>
        <div>
            <span class="{badge_style}">{comm_pct:.2f}% (Target: {target_sla}%)</span>
            <span style="font-size:0.75rem; color:#0f172a; font-weight:700; margin-left:6px;">{delta_symbol} {abs(comm_delta):.2f}% DoD</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    valid_pct = latest["validity_pct"]
    st.markdown(f"""
    <div class="pbi-card pbi-card-amber">
        <div class="pbi-title">Valid Reads ({latest[cols['date']].strftime('%d-%b')})</div>
        <div class="pbi-val">{int(latest[cols['valid']]):,}</div>
        <span class="badge-pass">{valid_pct:.2f}% Data Validity</span>
    </div>
    """, unsafe_allow_html=True)

with k4:
    billed_conv = latest["billed_conv_pct"]
    st.markdown(f"""
    <div class="pbi-card pbi-card-purple">
        <div class="pbi-title">Billed Reads ({latest[cols['date']].strftime('%d-%b')})</div>
        <div class="pbi-val">{int(latest[cols['billed']]):,}</div>
        <span class="badge-pass" style="background:#ede9fe; color:#6d28d9 !important;">{billed_conv:.2f}% of Received</span>
    </div>
    """, unsafe_allow_html=True)

# --- ROW 2: PRIMARY TREND CHARTS ---
t_col1, t_col2 = st.columns(2)

with t_col1:
    st.markdown("### 📈 Volume Trend: Fleet vs. Received vs. Billed")
    fig_vol = go.Figure()
    
    fig_vol.add_trace(go.Scatter(
        x=filtered_df[cols["date"]],
        y=filtered_df["total_meters"],
        mode="lines",
        name="Total Fleet",
        line=dict(color="#64748b", width=2, dash="dash")
    ))
    fig_vol.add_trace(go.Scatter(
        x=filtered_df[cols["date"]],
        y=filtered_df["received_meters"],
        mode="lines+markers",
        name="Received Meters",
        line=dict(color="#2563eb", width=2.5),
        marker=dict(size=6)
    ))
    fig_vol.add_trace(go.Scatter(
        x=filtered_df[cols["date"]],
        y=filtered_df[cols["valid"]],
        mode="lines",
        name="Valid Reads Only",
        line=dict(color="#10b981", width=2)
    ))
    fig_vol.add_trace(go.Scatter(
        x=filtered_df[cols["date"]],
        y=filtered_df[cols["billed"]],
        mode="lines+markers",
        name="Billed Reads",
        line=dict(color="#f59e0b", width=2.5),
        marker=dict(size=6)
    ))
    fig_vol.update_layout(
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#0f172a", family="Segoe UI, sans-serif", size=12),
        height=380,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1,
            font=dict(color="#0f172a", size=11, weight="bold")
        ),
        xaxis=dict(
            color="#0f172a",
            tickfont=dict(color="#0f172a", size=11),
            gridcolor="#e2e8f0",
            tickformat="%d %b"
        ),
        yaxis=dict(
            title=dict(text="Number of Smart Meters", font=dict(color="#0f172a", size=12)),
            color="#0f172a",
            tickfont=dict(color="#0f172a", size=11),
            gridcolor="#e2e8f0",
            range=[filtered_df[cols["billed"]].min() * 0.96, total_fleet_meters * 1.02],
            tickformat=","
        ),
        hovermode="x unified"
    )
    st.plotly_chart(fig_vol, use_container_width=True)

with t_col2:
    st.markdown("### 📊 Rates: Network SLA % vs. Billed Conversion %")
    fig_rates = go.Figure()
    
    fig_rates.add_hline(
        y=target_sla, 
        line_dash="dot", 
        line_color="#dc2626", 
        annotation_text=f"Target ({target_sla}%)", 
        annotation_position="bottom right",
        annotation_font=dict(color="#dc2626", size=11, weight="bold")
    )
    fig_rates.add_trace(go.Scatter(
        x=filtered_df[cols["date"]],
        y=filtered_df["comm_sla_pct"],
        mode="lines+markers",
        name="Comm SLA % (Rec / Total)",
        line=dict(color="#10b981", width=2.5),
        marker=dict(size=6, symbol="diamond")
    ))
    fig_rates.add_trace(go.Scatter(
        x=filtered_df[cols["date"]],
        y=filtered_df["billed_conv_pct"],
        mode="lines+markers",
        name="Billed Conversion % (Billed / Rec)",
        line=dict(color="#d97706", width=2.5),
        marker=dict(size=6, symbol="circle")
    ))
    fig_rates.update_layout(
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#0f172a", family="Segoe UI, sans-serif", size=12),
        height=380,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1,
            font=dict(color="#0f172a", size=11, weight="bold")
        ),
        xaxis=dict(
            color="#0f172a",
            tickfont=dict(color="#0f172a", size=11),
            gridcolor="#e2e8f0",
            tickformat="%d %b"
        ),
        yaxis=dict(
            title=dict(text="Percentage (%)", font=dict(color="#0f172a", size=12)),
            color="#0f172a",
            tickfont=dict(color="#0f172a", size=11),
            gridcolor="#e2e8f0",
            range=[85.0, 101.0],
            ticksuffix="%"
        ),
        hovermode="x unified"
    )
    st.plotly_chart(fig_rates, use_container_width=True)

# --- ROW 3: FIELD DEFECTS & DEDICATED DAY-WISE METER COMMUNICATION PIE ---
c_left, c_right = st.columns([3, 2])

with c_left:
    st.markdown("### 🔍 Daily Field Exceptions (Defect Decomposition)")
    fig_exc = go.Figure()
    fig_exc.add_trace(go.Bar(
        x=filtered_df[cols["date"]].dt.strftime("%d-%b"),
        y=filtered_df[cols["invalid"]],
        name="Invalid / Abnormal Reads",
        marker_color="#ef4444"
    ))
    fig_exc.add_trace(go.Bar(
        x=filtered_df[cols["date"]].dt.strftime("%d-%b"),
        y=filtered_df[cols["no_comm"]],
        name="Non-Communicating Meters",
        marker_color="#f97316"
    ))
    fig_exc.update_layout(
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#0f172a", family="Segoe UI, sans-serif", size=12),
        barmode="stack",
        height=370,
        margin=dict(l=20, r=20, t=15, b=20),
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1,
            font=dict(color="#0f172a", size=11, weight="bold")
        ),
        xaxis=dict(
            color="#0f172a",
            tickfont=dict(color="#0f172a", size=11),
            gridcolor="#e2e8f0",
            tickangle=-45
        ),
        yaxis=dict(
            title=dict(text="Exception Count", font=dict(color="#0f172a")),
            color="#0f172a",
            tickfont=dict(color="#0f172a", size=11),
            gridcolor="#e2e8f0",
            tickformat=","
        ),
        hovermode="x unified"
    )
    st.plotly_chart(fig_exc, use_container_width=True)

with c_right:
    # Dedicated Day-Wise Filter Control for Donut Chart
    date_options = filtered_df[cols["date"]].dt.date.tolist()
    default_date_idx = len(date_options) - 1
    
    col_chart_header, col_date_picker = st.columns([3, 2])
    with col_chart_header:
        st.markdown("### 📡 Communication Breakdown")
    with col_date_picker:
        selected_pie_date = st.selectbox(
            "Select Specific Day:",
            options=date_options,
            index=default_date_idx,
            format_func=lambda d: d.strftime("%d-%b-%Y")
        )

    # Filter for chosen single day
    day_row = filtered_df[filtered_df[cols["date"]].dt.date == selected_pie_date].iloc[0]
    
    valid_comm = int(day_row[cols["valid"]])
    invalid_comm = int(day_row[cols["invalid"]])
    no_comm = total_fleet_meters - (valid_comm + invalid_comm)
    
    comm_pie_df = pd.DataFrame({
        "Status": [
            "Valid Communicating", 
            "Invalid / Abnormal Packets", 
            "Non-Communicating Dropouts"
        ],
        "Count": [valid_comm, invalid_comm, no_comm]
    })
    
    fig_comm_pie = px.pie(
        comm_pie_df,
        names="Status",
        values="Count",
        hole=0.45,
        color="Status",
        color_discrete_map={
            "Valid Communicating": "#10b981",
            "Invalid / Abnormal Packets": "#ef4444",
            "Non-Communicating Dropouts": "#f97316"
        }
    )
    fig_comm_pie.update_layout(
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#0f172a", family="Segoe UI, sans-serif"),
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(
            orientation="h", 
            y=-0.2,
            font=dict(color="#0f172a", size=11, weight="bold")
        )
    )
    fig_comm_pie.update_traces(
        textposition="inside", 
        textinfo="percent",
        textfont=dict(color="#ffffff", size=13, weight="bold")
    )
    st.plotly_chart(fig_comm_pie, use_container_width=True)

# --- ROW 4: POWER BI MATRIX / AUDIT TABLE ---
st.markdown(f"### 📋 Reconciliation Matrix ({len(filtered_df)} Selected Reporting Cycles)")

grid_df = filtered_df[[
    cols["date"], "total_meters", "received_meters", cols["valid"], 
    cols["invalid"], cols["no_comm"], cols["billed"], "comm_sla_pct", "billed_conv_pct"
]].copy()
grid_df[cols["date"]] = grid_df[cols["date"]].dt.strftime("%d-%m-%Y")

st.dataframe(
    grid_df.style.format({
        "total_meters": "{:,.0f}",
        "received_meters": "{:,.0f}",
        cols["valid"]: "{:,.0f}",
        cols["invalid"]: "{:,.0f}",
        cols["no_comm"]: "{:,.0f}",
        cols["billed"]: "{:,.0f}",
        "comm_sla_pct": "{:.2f}%",
        "billed_conv_pct": "{:.2f}%"
    }),
    use_container_width=True,
    height=260
)

# Export Trigger
csv_buffer = io.StringIO()
grid_df.to_csv(csv_buffer, index=False)
st.download_button(
    label="📥 Export Current Filtered Slice (CSV)",
    data=csv_buffer.getvalue(),
    file_name=f"ami_sla_export_{start_date}_to_{end_date}.csv",
    mime="text/csv"
)