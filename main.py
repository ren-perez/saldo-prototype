import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Saldo - Transaction Categorizer",
    page_icon="🏷️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .category-card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.25rem 0;
        border-left: 4px solid #4A90E2;
        cursor: pointer;
        transition: all 0.2s ease;
        backdrop-filter: blur(10px);
    }
    .category-card:hover {
        background-color: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.2);
        transform: translateX(2px);
    }
    
    /* Uncategorized - Yellow */
    .uncategorized-row {
        background-color: rgba(255, 193, 7, 0.15);
        border: 1px solid rgba(255, 193, 7, 0.4);
        padding: 0.6rem;
        border-radius: 0.4rem;
        margin: 0.3rem 0;
        border-left: 4px solid #FFC107;
        backdrop-filter: blur(5px);
    }
    
    /* Categorized (default) - Gray */
    .categorized-row {
        background-color: rgba(108, 117, 125, 0.15);
        border: 1px solid rgba(108, 117, 125, 0.3);
        padding: 0.6rem;
        border-radius: 0.4rem;
        margin: 0.3rem 0;
        border-left: 4px solid #6C757D;
        backdrop-filter: blur(5px);
    }
    
    /* Positive amount - Green */
    .positive-amount-row {
        background-color: rgba(40, 167, 69, 0.15);
        border: 1px solid rgba(40, 167, 69, 0.3);
        padding: 0.6rem;
        border-radius: 0.4rem;
        margin: 0.3rem 0;
        border-left: 4px solid #28A745;
        backdrop-filter: blur(5px);
    }
    
    /* Negative amount - Red */
    .negative-amount-row {
        background-color: rgba(220, 53, 69, 0.15);
        border: 1px solid rgba(220, 53, 69, 0.3);
        padding: 0.6rem;
        border-radius: 0.4rem;
        margin: 0.3rem 0;
        border-left: 4px solid #DC3545;
        backdrop-filter: blur(5px);
    }
    
    /* Light theme compatibility */
    [data-theme="light"] .category-card {
        background-color: rgba(0, 0, 0, 0.02);
        border: 1px solid rgba(0, 0, 0, 0.08);
    }
    [data-theme="light"] .category-card:hover {
        background-color: rgba(0, 0, 0, 0.04);
        border-color: rgba(0, 0, 0, 0.12);
    }
    [data-theme="light"] .uncategorized-row {
        background-color: rgba(255, 193, 7, 0.1);
        border: 1px solid rgba(255, 193, 7, 0.25);
    }
    [data-theme="light"] .categorized-row {
        background-color: rgba(108, 117, 125, 0.1);
        border: 1px solid rgba(108, 117, 125, 0.2);
    }
    [data-theme="light"] .positive-amount-row {
        background-color: rgba(40, 167, 69, 0.1);
        border: 1px solid rgba(40, 167, 69, 0.25);
    }
    [data-theme="light"] .negative-amount-row {
        background-color: rgba(220, 53, 69, 0.1);
        border: 1px solid rgba(220, 53, 69, 0.25);
    }
</style>
""", unsafe_allow_html=True)

# Main navigation
st.title("🏷️ Saldo - Transaction Categorizer")

# Sidebar navigation
page = st.sidebar.selectbox(
    "Select Page:",
    ["Dashboard", "Categorize Transactions", "Manage Categories"]
)

# Import and display pages
if page == "Dashboard":
    import pages.dashboard as dashboard_page
    dashboard_page.show()
elif page == "Categorize Transactions":
    import pages.categorize_transactions as cat_page
    cat_page.show()
elif page == "Manage Categories":
    import pages.manage_categories as mgmt_page
    mgmt_page.show()