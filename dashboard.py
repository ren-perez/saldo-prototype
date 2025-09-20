import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Saldo - Personal Finance Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .expense-card {
        border-left-color: #ff6b6b;
    }
    .income-card {
        border-left-color: #51cf66;
    }
    .balance-card {
        border-left-color: #339af0;
    }
    .stSelectbox > label {
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and process financial data"""
    try:
        # Load main transactions data
        transactions_path = "data/processed/transactions.csv"
        if os.path.exists(transactions_path):
            df = pd.read_csv(transactions_path)
        else:
            # Create sample data if file doesn't exist
            df = create_sample_data()
        
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # Load metadata
        metadata = load_metadata()
        
        return df, metadata
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return create_sample_data(), {}

def create_sample_data():
    """Create sample data for demo purposes"""
    np.random.seed(42)
    
    # Generate sample transactions
    start_date = datetime.now() - timedelta(days=90)
    dates = pd.date_range(start=start_date, end=datetime.now(), freq='D')
    
    transactions = []
    transaction_types = ['Groceries', 'Transportation', 'Dining', 'Shopping', 'Bills', 'Income', 'Entertainment']
    
    for i, date in enumerate(dates):
        # Random number of transactions per day
        n_transactions = np.random.poisson(2)
        
        for j in range(n_transactions):
            trans_type = np.random.choice(transaction_types)
            
            if trans_type == 'Income':
                amount = np.random.uniform(500, 2000)
                transaction_type = 'Credit'
                description = f"Salary deposit"
            elif trans_type == 'Bills':
                amount = -np.random.uniform(50, 300)
                transaction_type = 'Debit'
                description = f"{trans_type} payment"
            else:
                amount = -np.random.uniform(5, 150)
                transaction_type = 'Debit'
                description = f"{trans_type} purchase"
            
            transactions.append({
                'id': f"{i}_{j}",
                'date': date,
                'description': description,
                'amount': amount,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'account_id': np.random.choice([16, 17, 18]),
                'category_id': hash(trans_type) % 10,
                'transaction_type': transaction_type,
                'category': trans_type
            })
    
    return pd.DataFrame(transactions)

@st.cache_data
def load_metadata():
    """Load metadata files"""
    metadata = {}
    
    # Sample accounts
    metadata['accounts'] = pd.DataFrame({
        'account_id': [16, 17, 18],
        'account_name': ['Checking Account', 'Savings Account', 'Credit Card'],
        'bank': ['Chase', 'Wells Fargo', 'Amex'],
        'currency': ['USD', 'USD', 'USD']
    })
    
    # Sample categories
    metadata['categories'] = pd.DataFrame({
        'id': range(10),
        'name': ['Groceries', 'Transportation', 'Dining', 'Shopping', 'Bills', 
                'Income', 'Entertainment', 'Healthcare', 'Education', 'Other'],
        'group_id': [1, 2, 2, 2, 1, 3, 2, 1, 1, 2]
    })
    
    # Category groups
    metadata['category_groups'] = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Essentials', 'Discretionary', 'Income']
    })
    
    return metadata

def calculate_kpis(df, start_date, end_date):
    """Calculate key performance indicators"""
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    total_income = filtered_df[filtered_df['amount'] > 0]['amount'].sum()
    total_expenses = abs(filtered_df[filtered_df['amount'] < 0]['amount'].sum())
    net_balance = total_income - total_expenses
    
    # Previous period comparison
    period_days = (end_date - start_date).days
    prev_start = start_date - timedelta(days=period_days)
    prev_end = start_date
    
    prev_df = df[(df['date'] >= prev_start) & (df['date'] < prev_end)]
    prev_expenses = abs(prev_df[prev_df['amount'] < 0]['amount'].sum())
    
    expense_change = ((total_expenses - prev_expenses) / prev_expenses * 100) if prev_expenses > 0 else 0
    
    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_balance': net_balance,
        'expense_change': expense_change
    }

def create_time_series_chart(df):
    """Create time series chart for cash flow"""
    daily_flow = df.groupby('date')['amount'].sum().reset_index()
    daily_flow['cumulative'] = daily_flow['amount'].cumsum()
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Daily Cash Flow', 'Cumulative Balance'),
        vertical_spacing=0.1,
        row_heights=[0.6, 0.4]
    )
    
    # Daily cash flow
    colors = ['red' if x < 0 else 'green' for x in daily_flow['amount']]
    fig.add_trace(
        go.Bar(
            x=daily_flow['date'],
            y=daily_flow['amount'],
            name='Daily Flow',
            marker_color=colors,
            opacity=0.7
        ),
        row=1, col=1
    )
    
    # Cumulative balance
    fig.add_trace(
        go.Scatter(
            x=daily_flow['date'],
            y=daily_flow['cumulative'],
            name='Cumulative Balance',
            line=dict(color='blue', width=2),
            fill='tonexty'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        title_text="Cash Flow Analysis"
    )
    
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Amount ($)", row=1, col=1)
    fig.update_yaxes(title_text="Balance ($)", row=2, col=1)
    
    return fig

def create_category_chart(df):
    """Create category spending breakdown"""
    expenses_df = df[df['amount'] < 0].copy()
    expenses_df['amount'] = abs(expenses_df['amount'])
    
    if 'category' not in expenses_df.columns:
        expenses_df['category'] = 'Other'
    
    category_spending = expenses_df.groupby('category')['amount'].sum().reset_index()
    category_spending = category_spending.sort_values('amount', ascending=False)
    
    fig = px.pie(
        category_spending,
        values='amount',
        names='category',
        title='Spending by Category',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Amount: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
    )
    
    fig.update_layout(height=400)
    
    return fig

def create_monthly_trend(df, current_start_date, current_end_date):
    """Create monthly spending trend with current month highlighted"""
    df_monthly = df.copy()
    df_monthly['month'] = df_monthly['date'].dt.to_period('M')
    
    monthly_summary = df_monthly.groupby('month').agg({
        'amount': lambda x: (x[x > 0].sum(), abs(x[x < 0].sum()))
    }).reset_index()
    
    monthly_summary[['income', 'expenses']] = pd.DataFrame(
        monthly_summary['amount'].tolist(), 
        index=monthly_summary.index
    )
    monthly_summary['month_str'] = monthly_summary['month'].astype(str)
    
    # Determine current month for highlighting
    current_period = pd.Period(current_start_date, 'M')
    current_month_str = str(current_period)
    
    fig = go.Figure()
    
    # Add income bars
    fig.add_trace(go.Bar(
        x=monthly_summary['month_str'],
        y=monthly_summary['income'],
        name='Income',
        marker_color=['lightgreen' if month == current_month_str else 'green' 
                     for month in monthly_summary['month_str']],
        opacity=0.8
    ))
    
    # Add expense bars
    fig.add_trace(go.Bar(
        x=monthly_summary['month_str'],
        y=monthly_summary['expenses'],
        name='Expenses',
        marker_color=['lightcoral' if month == current_month_str else 'red' 
                     for month in monthly_summary['month_str']],
        opacity=0.8
    ))
    
    fig.update_layout(
        title=f'Monthly Trend (Current: {current_month_str})',
        xaxis_title='Month',
        yaxis_title='Amount ($)',
        barmode='group',
        height=400,
        hovermode='x unified'
    )
    
    return fig

def main():
    st.title("💰 Saldo - Personal Finance Dashboard")
    st.markdown("Track your expenses, analyze spending patterns, and manage your finances effectively.")
    
    # Load data
    df, metadata = load_data()
    
    if df.empty:
        st.error("No transaction data available. Please check your data files.")
        return
    
    # Sidebar filters
    st.sidebar.header("🔧 Filters")
    
    # Month Navigator - Primary Time Control
    st.sidebar.subheader("📅 Time Navigator")
    
    # Get available months
    df['year_month'] = df['date'].dt.to_period('M')
    available_months = sorted(df['year_month'].unique(), reverse=True)
    available_month_strings = [str(month) for month in available_months]
    
    # Navigation method selector
    nav_method = st.sidebar.radio(
        "Navigation Style:",
        ["Month Navigator", "Custom Date Range"],
        index=0
    )
    
    if nav_method == "Month Navigator":
        # Current month selection
        current_month_idx = 0 if available_month_strings else 0
        
        col1, col2, col3 = st.sidebar.columns([1, 2, 1])
        
        with col1:
            if st.button("◀️", help="Previous month"):
                if current_month_idx < len(available_month_strings) - 1:
                    current_month_idx += 1
        
        with col3:
            if st.button("▶️", help="Next month"):
                if current_month_idx > 0:
                    current_month_idx -= 1
        
        # Month selector dropdown
        selected_month_str = st.sidebar.selectbox(
            "Select Month:",
            options=available_month_strings,
            index=current_month_idx,
            key="month_selector"
        )
        
        # Convert back to datetime for filtering
        selected_period = pd.Period(selected_month_str)
        start_date = selected_period.start_time.date()
        end_date = selected_period.end_time.date()
        
        st.sidebar.success(f"📊 Viewing: **{selected_month_str}**")
        
        # Quick month jumpers
        st.sidebar.markdown("**Quick Jump:**")
        quick_col1, quick_col2 = st.sidebar.columns(2)
        with quick_col1:
            if st.button("This Month"):
                current_period = pd.Period.now('M')
                if str(current_period) in available_month_strings:
                    st.session_state.month_selector = str(current_period)
                    st.experimental_rerun()
        
        with quick_col2:
            if st.button("Last Month"):
                last_period = pd.Period.now('M') - 1
                if str(last_period) in available_month_strings:
                    st.session_state.month_selector = str(last_period)
                    st.experimental_rerun()
    
    else:  # Custom Date Range
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(max_date - timedelta(days=30), max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = end_date = date_range[0]
    
    # Account filter
    if 'accounts' in metadata and not metadata['accounts'].empty:
        account_names = metadata['accounts']['account_name'].tolist()
        selected_accounts = st.sidebar.multiselect(
            "Select Accounts",
            options=account_names,
            default=account_names
        )
        
        # Filter by selected accounts
        account_ids = metadata['accounts'][
            metadata['accounts']['account_name'].isin(selected_accounts)
        ]['account_id'].tolist()
        
        df_filtered = df[df['account_id'].isin(account_ids)]
    else:
        df_filtered = df
    
    # Category filter
    if 'category' in df_filtered.columns:
        categories = df_filtered['category'].unique().tolist()
        selected_categories = st.sidebar.multiselect(
            "Select Categories",
            options=categories,
            default=categories
        )
        df_filtered = df_filtered[df_filtered['category'].isin(selected_categories)]
    
    # Apply date filter
    df_filtered = df_filtered[
        (df_filtered['date'] >= pd.to_datetime(start_date)) &
        (df_filtered['date'] <= pd.to_datetime(end_date))
    ]
    
    # Fix transaction count - count unique transactions
    total_transactions = len(df_filtered)
    
    # Calculate KPIs
    kpis = calculate_kpis(df_filtered, pd.to_datetime(start_date), pd.to_datetime(end_date))
    
    # Display KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💚 Total Income",
            value=f"${kpis['total_income']:,.2f}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="💸 Total Expenses",
            value=f"${kpis['total_expenses']:,.2f}",
            delta=f"{kpis['expense_change']:.1f}%" if kpis['expense_change'] != 0 else None,
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="💰 Net Balance",
            value=f"${kpis['net_balance']:,.2f}",
            delta=None,
            delta_color="normal" if kpis['net_balance'] >= 0 else "inverse"
        )
    
    with col4:
        avg_daily = kpis['total_expenses'] / ((pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1)
        st.metric(
            label="📊 Avg Daily Spend",
            value=f"${avg_daily:.2f}",
            delta=None
        )
    
    # Main charts
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.plotly_chart(create_time_series_chart(df_filtered), use_container_width=True)
    
    with col2:
        st.plotly_chart(create_category_chart(df_filtered), use_container_width=True)
    
    # Monthly trend
    st.plotly_chart(create_monthly_trend(df, start_date, end_date), use_container_width=True)
    
    # Month-over-Month comparison (only show if in month navigator mode)
    if nav_method == "Month Navigator" and len(available_months) > 1:
        st.markdown("---")
        st.subheader("📊 Month-over-Month Analysis")
        
        # Get previous month data for comparison
        current_period = pd.Period(selected_month_str)
        prev_period = current_period - 1
        
        if str(prev_period) in available_month_strings:
            # Current month data
            current_data = df[df['year_month'] == current_period]
            current_expenses = abs(current_data[current_data['amount'] < 0]['amount'].sum())
            current_income = current_data[current_data['amount'] > 0]['amount'].sum()
            
            # Previous month data  
            prev_data = df[df['year_month'] == prev_period]
            prev_expenses = abs(prev_data[prev_data['amount'] < 0]['amount'].sum())
            prev_income = prev_data[prev_data['amount'] > 0]['amount'].sum()
            
            # Calculate changes
            expense_change = ((current_expenses - prev_expenses) / prev_expenses * 100) if prev_expenses > 0 else 0
            income_change = ((current_income - prev_income) / prev_income * 100) if prev_income > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    f"Income vs {prev_period}",
                    f"${current_income:,.2f}",
                    f"{income_change:+.1f}%"
                )
            
            with col2:
                st.metric(
                    f"Expenses vs {prev_period}",
                    f"${current_expenses:,.2f}",
                    f"{expense_change:+.1f}%",
                    delta_color="inverse"
                )
            
            with col3:
                savings_rate_current = ((current_income - current_expenses) / current_income * 100) if current_income > 0 else 0
                savings_rate_prev = ((prev_income - prev_expenses) / prev_income * 100) if prev_income > 0 else 0
                savings_change = savings_rate_current - savings_rate_prev
                
                st.metric(
                    "Savings Rate",
                    f"{savings_rate_current:.1f}%",
                    f"{savings_change:+.1f}pp"
                )
            
            with col4:
                transaction_change = len(current_data) - len(prev_data)
                st.metric(
                    "Transactions",
                    len(current_data),
                    f"{transaction_change:+d}"
                )
    
    # Recent transactions table
    st.markdown("---")
    st.subheader("📋 Recent Transactions")
    
    recent_transactions = df_filtered.nlargest(10, 'date')[
        ['date', 'description', 'amount', 'transaction_type']
    ].copy()
    
    # Format the display
    recent_transactions['date'] = recent_transactions['date'].dt.strftime('%Y-%m-%d')
    recent_transactions['amount'] = recent_transactions['amount'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(
        recent_transactions,
        use_container_width=True,
        hide_index=True
    )
    
    # Summary statistics
    st.markdown("---")
    st.subheader("📈 Summary Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Transaction Count:**", total_transactions)
        st.write("**Date Range:**", f"{start_date} to {end_date}")
        
        # Show period context
        if nav_method == "Month Navigator":
            days_in_period = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1
            st.write("**Days in Period:**", days_in_period)
    
    with col2:
        if len(df_filtered) > 0:
            st.write("**Largest Expense:**", f"${abs(df_filtered[df_filtered['amount'] < 0]['amount'].min()):,.2f}")
            st.write("**Largest Income:**", f"${df_filtered[df_filtered['amount'] > 0]['amount'].max():,.2f}")
    
    with col3:
        if len(df_filtered) > 0:
            expenses = df_filtered[df_filtered['amount'] < 0]['amount']
            if len(expenses) > 0:
                st.write("**Avg Transaction:**", f"${abs(expenses.mean()):,.2f}")
                st.write("**Median Transaction:**", f"${abs(expenses.median()):,.2f}")

if __name__ == "__main__":
    main()