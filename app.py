

import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# Load CSV
# -----------------------------
df = pd.read_csv("water_quality.csv")

# -----------------------------
# WHO/FAO Guidelines (simplified example)
# -----------------------------
guidelines = {
    "pH": (6.5, 8.4),                # acceptable range
    "EC": (None, 3000),              # µS/cm, <3000 safe for general crops
    "Nitrate": (None, 10),           # mg/L, <10 safe
    "Phosphate": (None, 2),          # mg/L, <2 preferred
    "Iron": (None, 5),               # mg/L, <5 safe
    "Turbidity": (None, 5),          # NTU, <5 for drip irrigation
    "COD": (None, 250),              # mg/L, indicative threshold
    "BOD": (None, 20),               # mg/L, indicative threshold
    "DO": (5, None),                 # mg/L, desirable >5
    "E. coli": (None, 100),          # CFU/100mL, unrestricted irrigation
    "Fecal coliforms": (None, 1000)  # CFU/100mL, restricted irrigation
}

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filters")
selected_site = st.sidebar.multiselect("Select Site(s):", df["Site"].unique(), default=df["Site"].unique())
selected_campaign = st.sidebar.multiselect("Select Campaign(s):", df["Campaign"].unique(), default=df["Campaign"].unique())

filtered_df = df[
    (df["Site"].isin(selected_site)) &
    (df["Campaign"].isin(selected_campaign))
]

# -----------------------------
# Descriptive Statistics
# -----------------------------
st.subheader("📊 Descriptive Statistics (Numeric Only)")
numeric_df = filtered_df.select_dtypes(include="number")
if not numeric_df.empty:
    st.write(numeric_df.describe())
else:
    st.warning("No numeric data available for descriptive statistics.")

st.markdown("---")

# -----------------------------
# Correlation Analysis
# -----------------------------
st.subheader("🔗 Parameter Correlations (Numeric Only)")
if not numeric_df.empty:
    corr = numeric_df.corr()
    st.write(corr)

    fig_corr = px.imshow(corr,
                         text_auto=True,
                         aspect="auto",
                         color_continuous_scale="RdBu_r",
                         title="Correlation Heatmap of Parameters")
    st.plotly_chart(fig_corr, use_container_width=True)
else:
    st.warning("No numeric data available for correlation analysis.")

st.markdown("---")

# -----------------------------
# Trend Analysis with Guidelines
# -----------------------------
st.subheader("📈 Parameter Trends vs WHO Guidelines")

# Reshape wide → long for plotting
long_df = df.melt(id_vars=["Site", "Campaign"],
                  value_vars=[col for col in df.columns if col not in ["Site", "Campaign"]],
                  var_name="Parameter",
                  value_name="Value")

selected_parameter = st.sidebar.selectbox("Select Parameter:", long_df["Parameter"].unique())

param_df = long_df[
    (long_df["Site"].isin(selected_site)) &
    (long_df["Campaign"].isin(selected_campaign)) &
    (long_df["Parameter"] == selected_parameter)
]

if not param_df.empty:
    avg_val = param_df["Value"].mean()
    st.metric(f"Average {selected_parameter}", f"{avg_val:.2f}")

    # Check guideline
    if selected_parameter in guidelines:
        low, high = guidelines[selected_parameter]
        if (low is not None and avg_val < low) or (high is not None and avg_val > high):
            st.error(f"⚠️ Average {selected_parameter} ({avg_val:.2f}) exceeds WHO/FAO guideline!")
        else:
            st.success(f"✅ Average {selected_parameter} is within WHO/FAO guideline.")

    # Bar graph by site
    fig_bar = px.bar(param_df, x="Site", y="Value", color="Site",
                     title=f"{selected_parameter} Levels by Site")
    st.plotly_chart(fig_bar, use_container_width=True)

    # Line graph by campaign
    fig_line = px.line(param_df, x="Campaign", y="Value", color="Site",
                       markers=True, title=f"{selected_parameter} Trends Over Campaigns")
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.warning("No data available for the selected parameter.")

