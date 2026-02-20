import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import plotly.express as px

# Import pipeline components
from main import process_search, process_single_url
from config.settings import DEFAULT_OUTPUT_DIR

# ──────────────────────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FOA Intelligence Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for premium look
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    .tag-chip {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 15px;
        background-color: #e9ecef;
        margin: 2px;
        font-size: 0.8em;
        border: 1px solid #dee2e6;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🧠 FOA Intelligence")
    st.markdown("---")
    
    st.header("Search Settings")
    source = st.selectbox("Data Source", ["grants_gov", "nsf"], index=1)
    max_results = st.slider("Max Results", 1, 50, 10)
    use_embeddings = st.checkbox("Use Semantic Embeddings", value=False, help="Requires sentence-transformers")
    
    st.markdown("---")
    st.info("""
    **GSoC 2026 Submission**
    Organization: Human AI Foundation
    Project: FOA Ingestion + Semantic Tagging
    """)

# ──────────────────────────────────────────────────────────────
# Main UI
# ──────────────────────────────────────────────────────────────
st.title("🔍 Funding Opportunity Discovery")
st.markdown("Discover, extract, and semantically tag funding opportunities in real-time.")

tab1, tab2 = st.tabs(["Keyword Search", "Direct URL Ingestion"])

# --- Tab 1: Keyword Search ---
with tab1:
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input("Enter keywords (e.g., 'artificial intelligence', 'climate change')", "")
    with col2:
        st.write("") # Padding
        st.write("")
        search_btn = st.button("Search")

    if search_btn and query:
        with st.spinner(f"Searching {source} for '{query}'..."):
            try:
                records = process_search(
                    keyword=query,
                    source=source,
                    max_results=max_results,
                    use_embeddings=use_embeddings
                )
                st.session_state['records'] = records
            except Exception as e:
                st.error(f"Search failed: {e}")

# --- Tab 2: URL Ingestion ---
with tab2:
    url_input = st.text_input("Enter FOA URL (Grants.gov or NSF)", "")
    ingest_btn = st.button("Analyze URL")
    
    if ingest_btn and url_input:
        with st.spinner("Analyzing opportunity..."):
            try:
                record = process_single_url(url_input, use_embeddings=use_embeddings)
                st.session_state['records'] = [record]
            except Exception as e:
                st.error(f"Analysis failed: {e}")

# ──────────────────────────────────────────────────────────────
# Results Display
# ──────────────────────────────────────────────────────────────
if 'records' in st.session_state and st.session_state['records']:
    records = st.session_state['records']
    
    # Summary Metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Ingested", len(records))
    with m2:
        agencies = set(r.agency for r in records)
        st.metric("Agencies", len(agencies))
    with m3:
        total_tags = sum(len(r.semantic_tags) for r in records)
        st.metric("Total Tags", total_tags)
    with m4:
        avg_tags = total_tags / len(records)
        st.metric("Avg Tags/FOA", f"{avg_tags:.1f}")

    # Visualizations
    st.markdown("---")
    v_col1, v_col2 = st.columns(2)
    
    with v_col1:
        # Tag distribution
        all_tags = []
        for r in records:
            all_tags.extend([t.tag.split('/')[-1] for t in r.semantic_tags])
        
        if all_tags:
            tag_df = pd.DataFrame(all_tags, columns=['Tag']).value_counts().reset_index()
            tag_df.columns = ['Tag', 'Count']
            fig = px.bar(tag_df, x='Count', y='Tag', orientation='h', title="Top Semantic Tags",
                         color_discrete_sequence=['#007bff'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tags identified yet for visualization.")
            
    with v_col2:
        # Agency distribution
        agency_df = pd.DataFrame([r.agency for r in records], columns=['Agency']).value_counts().reset_index()
        agency_df.columns = ['Agency', 'Count']
        fig = px.pie(agency_df, values='Count', names='Agency', title="Agency Distribution")
        st.plotly_chart(fig, use_container_width=True)

    # Detailed Table
    st.header("Results Detail")
    
    for i, r in enumerate(records):
        with st.expander(f"{r.title[:100]}... [{'ID: ' + r.foa_id}]"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.write(f"**Agency:** {r.agency}")
                st.write(f"**Source:** {r.source.upper()}")
                st.write(f"**Open Date:** {r.open_date}")
                st.write(f"**Close Date:** {r.close_date}")
                st.markdown(f"**Source URL:** [{r.source_url}]({r.source_url})")
            
            with c2:
                st.write("**Semantic Tags:**")
                if r.semantic_tags:
                    for t in r.semantic_tags:
                        st.markdown(f"<span class='tag-chip'>{t.tag} ({t.confidence:.2f})</span>", unsafe_allow_html=True)
                else:
                    st.write("No tags identified.")
            
            st.markdown("---")
            st.write("**Program Description Snippet:**")
            desc = r.program_description or "No description available."
            st.write(desc[:500] + "..." if len(desc) > 500 else desc)

    # Export Options
    st.sidebar.markdown("---")
    st.sidebar.header("Export Data")
    
    # JSON Export
    json_data = json.dumps([r.model_dump(mode="json") for r in records], indent=2)
    st.sidebar.download_button(
        label="Download JSON",
        data=json_data,
        file_name=f"foa_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json"
    )
    
    # CSV Export
    df = pd.DataFrame([r.to_flat_dict() for r in records])
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="Download CSV",
        data=csv_data,
        file_name=f"foa_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

elif 'records' in st.session_state:
    st.warning("No results found for your search criteria.")
else:
    st.info("👈 Enter search keywords in the sidebar or above to start discovering funding opportunities.")
