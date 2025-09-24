# app.py (Updated)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import tempfile
import os
from contract_analyzer import analyze_contract_file
from pdf_generator import generate_rewritten_pdf

st.set_page_config(
    page_title="AI-Powered Compliance Dashboard",
    page_icon="⚖️",
    layout="wide"
)

def initialize_session_state():
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'contract_name' not in st.session_state:
        st.session_state.contract_name = ""

def analyze_contract(uploaded_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        with st.spinner("Analyzing contract... This may take a few minutes."):
            analysis_results = analyze_contract_file(tmp_file_path)
        os.unlink(tmp_file_path)
        if analysis_results:
            st.success("Analysis complete!")
            return analysis_results
        else:
            st.error("Failed to analyze contract")
            return None
    except Exception as e:
        st.error(f"Error during analysis: {str(e)}")
        return None

def create_dashboard(results):
    st.header("📊 Dashboard")
    df = pd.DataFrame(results)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Risk Levels")
        risk_counts = df['risk_level'].value_counts()
        fig_risk = px.bar(
            x=risk_counts.index,
            y=risk_counts.values,
            color=risk_counts.index,
            color_discrete_map={'High': '#ff4444', 'Medium': '#ffaa00', 'Low': '#44ff44'},
            title="Risk Level Distribution"
        )
        st.plotly_chart(fig_risk, use_container_width=True)
    with col2:
        st.subheader("Compliance Status")
        total_clauses = len(results)
        compliant = len([r for r in results if r['risk_level'] == 'Low'])
        non_compliant = total_clauses - compliant
        fig_compliance = go.Figure(data=[go.Pie(
            labels=['Compliant', 'Non-Compliant'],
            values=[compliant, non_compliant],
            hole=0.3,
            marker_colors=['#44ff44', '#ff4444']
        )])
        fig_compliance.update_layout(title="Compliance Ratio")
        st.plotly_chart(fig_compliance, use_container_width=True)
    st.subheader("Quick Stats")
    compliant_percentage = (compliant / total_clauses) * 100 if total_clauses > 0 else 0
    high_risk_count = len([r for r in results if r['risk_level'] == 'High'])
    risk_percentages = []
    for r in results:
        try:
            risk_val = r['risk_percent'].replace('%', '').strip()
            risk_percentages.append(float(risk_val))
        except:
            continue
    avg_risk = sum(risk_percentages) / len(risk_percentages) if risk_percentages else 0
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Clauses", len(results))
    with col2:
        st.metric("Compliance Rate", f"{compliant_percentage:.0f}%")
    with col3:
        st.metric("High Risk Clauses", high_risk_count)
    with col4:
        st.metric("Avg Risk Score", f"{avg_risk:.0f}%")
    if compliant > 0:
        st.success(f"✓ {compliant} clauses compliant")
    else:
        st.warning("⚠️ No fully compliant clauses found")

def create_summary_insights(results):
    st.header("📋 Summary & Insights")
    st.subheader("Contract Summary")
    st.write("This contract covers data handling, security controls, encryption, and liability.")
    gdpr_issues = len([r for r in results if 'GDPR' in r.get('regulation', '')])
    hipaa_issues = len([r for r in results if 'HIPAA' in r.get('regulation', '')])
    high_risk = len([r for r in results if r['risk_level'] == 'High'])
    summary_points = []
    if gdpr_issues > 0:
        summary_points.append("Data retention terms conflict with GDPR.")
    if hipaa_issues > 0:
        summary_points.append("Access control and encryption measures are compliant.")
    if high_risk > 0:
        summary_points.append("Liability clause is missing, which may increase legal risks.")
    for point in summary_points:
        st.write(f"• {point}")
    st.subheader("⚠️ Key Points to Consider")
    recommendations = []
    if gdpr_issues > 0:
        recommendations.append("Update retention policy to match GDPR timelines.")
    if any('liability' in r.get('key_clauses', '').lower() for r in results):
        recommendations.append("Include liability clause to reduce legal exposure.")
    if recommendations:
        for rec in recommendations:
            st.warning(f"• {rec}")
    else:
        st.success("• All clauses appear to be in good standing.")
    st.subheader("💡 Recommendation")
    high_risk_items = [r for r in results if r['risk_level'] == 'High']
    medium_risk_items = [r for r in results if r['risk_level'] == 'Medium']
    total_count = len(results)
    if high_risk_items:
        st.error("🚫 Do NOT accept this contract in current form. Review highlighted clauses before approval.")
    elif len(medium_risk_items) > total_count * 0.5:
        st.warning("⚠️ Review recommended changes before proceeding with contract approval.")
    else:
        st.success("✅ Contract appears acceptable with minor considerations.")
    st.subheader("Analysis Results")
    display_data = []
    for i, result in enumerate(results):
        display_data.append({
            'Clause ID': result['clause_id'],
            'Risk Level': result['risk_level'],
            'Compliant': '✓' if result['risk_level'] == 'Low' else '✗',
            'Comments': result['summary'][:50] + '...' if len(result['summary']) > 50 else result['summary']
        })
    display_df = pd.DataFrame(display_data)
    st.dataframe(display_df, use_container_width=True)

    
    st.markdown("---")
    st.subheader("⚡ AI-Rewritten Clauses")
    if "show_rewrites" not in st.session_state:
        st.session_state.show_rewrites = False
    if not st.session_state.show_rewrites:
        if st.button("✍️ Show AI-Generated Modifications"):
            st.session_state.show_rewrites = True
            st.rerun()
    if st.session_state.show_rewrites:
        df = pd.DataFrame(results)
        high_risk_df = df[df["risk_level"].isin(["High", "Medium"])].copy()
        if high_risk_df.empty:
            st.info("✅ No high-risk clauses were found to rewrite.")
        else:
            display_columns = {
                "clause_id": "Clause ID",
                "clause": "Original Clause",
                "AI-Modified Clause": "AI-Modified Clause",
                "AI-Modified Risk Level": "New Risk Level"
            }
            sugg_df = high_risk_df[list(display_columns.keys())].rename(columns=display_columns)
            st.dataframe(sugg_df, use_container_width=True, height=400)
            pdf_data = generate_rewritten_pdf(high_risk_df)
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_data,
                file_name="ai_rewritten_clauses_report.pdf",
                mime="application/pdf",
            )
   

def main():
    initialize_session_state()
    st.title("⚖️ AI-Powered Compliance Dashboard ⚖️")
    st.write("Upload your contract • Analyze • View results in an elegant dashboard")
    if not st.session_state.analysis_complete:
        st.markdown("---")
        st.subheader("📁 Upload a Contract")
        uploaded_file = st.file_uploader(
            "Drag and drop file here",
            type=['pdf', 'docx'],
            help="Limit 200MB per file • PDF, DOCX"
        )
        if uploaded_file is not None:
            st.success(f"✅ Uploaded: {uploaded_file.name}")
            st.session_state.contract_name = uploaded_file.name
            if st.button("🔍 Submit for Analysis", type="primary"):
                with st.spinner("Analyzing contract... This may take a few minutes."):
                    results = analyze_contract(uploaded_file)
                    if results:
                        st.session_state.analysis_results = results
                        st.session_state.analysis_complete = True
                        st.success("✅ Contract analyzed successfully!")
                        st.rerun()
    if st.session_state.analysis_complete and st.session_state.analysis_results:
        st.success("✅ Contract analyzed successfully!")
        tab1, tab2 = st.tabs(["📊 Dashboard", "📋 Summary & Insights"])
        with tab1:
            create_dashboard(st.session_state.analysis_results)
        with tab2:
            create_summary_insights(st.session_state.analysis_results)
        st.markdown("---")
        if st.button("🔄 Analyze Another Contract"):
            st.session_state.analysis_complete = False
            st.session_state.analysis_results = None
            st.session_state.contract_name = ""
            st.rerun()

if __name__ == "__main__":
    main()