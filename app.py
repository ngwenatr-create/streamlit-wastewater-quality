import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# Load datasets (Excel files)
# -----------------------------
physico_df = pd.read_excel("water_quality.xlsx")
amr_water_df = pd.read_excel("water_samples.xlsx")
amr_soil_df = pd.read_excel("soil_samples.xlsx")

# -----------------------------
# WHO/FAO Guidelines (simplified)
# -----------------------------
guidelines = {
    "pH": (6.5, 8.4),
    "EC": (None, 3000),
    "NO3": (None, 10),
    "PO4": (None, 2),
    "Fe": (None, 5),
    "NTU": (None, 5),
    "COD": (None, 250),
    "BOD": (None, 20),
    "DO": (5, None),
    "E.coli": (None, 100),
    "F coliforms": (None, 1000)
}

# -----------------------------
# Tabs
# -----------------------------
tab1, tab2 = st.tabs(["🌊 Physicochemical Parameters", "🦠 Antimicrobial Resistance"])

# -----------------------------
# Physicochemical Parameters Tab
# -----------------------------
with tab1:
    st.header("🌊 Physicochemical Parameters")

    # Sidebar filters
    st.sidebar.header("Filters")
    selected_site = st.sidebar.multiselect("Select Site(s):", physico_df["Site"].unique(), default=physico_df["Site"].unique())
    selected_campaign = st.sidebar.multiselect("Select Campaign(s):", physico_df["Campaign"].unique(), default=physico_df["Campaign"].unique())

    filtered_df = physico_df[
        (physico_df["Site"].isin(selected_site)) &
        (physico_df["Campaign"].isin(selected_campaign))
    ]

    # Descriptive statistics
    st.subheader("📊 Descriptive Statistics")
    numeric_df = filtered_df.select_dtypes(include="number")
    if not numeric_df.empty:
        st.write(numeric_df.describe())
    else:
        st.warning("No numeric data available.")

    st.markdown("---")

    # Correlation analysis
    st.subheader("🔗 Parameter Correlations")
    if not numeric_df.empty:
        corr = numeric_df.corr()
        fig_corr = px.imshow(corr, text_auto=True, aspect="auto",
                             color_continuous_scale="RdBu_r",
                             title="Correlation Heatmap")
        st.plotly_chart(fig_corr, use_container_width=True)

    st.markdown("---")

    # Trend analysis vs guidelines
    st.subheader("📈 Parameter Trends vs WHO Guidelines")
    long_df = physico_df.melt(id_vars=["Site", "Campaign"],
                              value_vars=[col for col in physico_df.columns if col not in ["Site", "Campaign"]],
                              var_name="Parameter", value_name="Value")

    selected_parameter = st.sidebar.selectbox("Select Parameter:", long_df["Parameter"].unique())
    param_df = long_df[
        (long_df["Site"].isin(selected_site)) &
        (long_df["Campaign"].isin(selected_campaign)) &
        (long_df["Parameter"] == selected_parameter)
    ]

    if not param_df.empty:
        param_df["Value_num"] = pd.to_numeric(param_df["Value"], errors="coerce")
        avg_val = param_df["Value_num"].mean()

        if not pd.isna(avg_val):
            st.metric(f"Average {selected_parameter}", f"{avg_val:.2f}")
        else:
            st.warning(f"{selected_parameter} is categorical (R/I/S). Showing counts instead.")
            st.bar_chart(param_df["Value"].value_counts())

        # Guideline check
        if selected_parameter in guidelines and not pd.isna(avg_val):
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

    # -----------------------------
# Antimicrobial Resistance Tab
# -----------------------------
with tab2:
    st.header("🦠 Antimicrobial Resistance (AMR)")
    st.write("AMR tab loaded ✅")  # Debug check

    # Sidebar filters (scoped to AMR tab)
    with st.sidebar:
        st.subheader("AMR Filters")
        sample_type = st.radio(
            "Select Sample Type:",
            ["Water", "Soil"],
            key="amr_sample_type"
        )

    # Choose dataset based on sample type
    df_amr = amr_water_df if sample_type == "Water" else amr_soil_df

    # Preview dataset
    st.write("Preview of AMR dataset:")
    st.dataframe(df_amr.head())

    # Organism filter
    with st.sidebar:
        organism = st.selectbox(
            "Select Organism:",
            df_amr["Organism"].unique(),
            key="amr_organism"
        )

    filtered_amr = df_amr[df_amr["Organism"] == organism]

    st.subheader(f"Resistance profile for {organism}")
    st.dataframe(filtered_amr)

    # Detect antibiotic columns automatically
    antibiotic_cols = [col for col in df_amr.columns if col not in ["Site", "Campaign", "Organism"]]

    # Map R/I/S → numeric
    mapping = {"R": 2, "I": 1, "S": 0}
    heatmap_df = filtered_amr[antibiotic_cols].replace(mapping)

    if not heatmap_df.empty:
        # Heatmap
        fig_heat = px.imshow(
            heatmap_df,
            labels=dict(color="Resistance Level (R=2, I=1, S=0)"),
            aspect="auto",
            color_continuous_scale="RdBu"
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        # Resistance counts per antibiotic
        summary = (filtered_amr[antibiotic_cols] == "R").sum()
        fig_bar = px.bar(
            summary,
            x=summary.index,
            y=summary.values,
            title="Number of Resistances per Antibiotic"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
