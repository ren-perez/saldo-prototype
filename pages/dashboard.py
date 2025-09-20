import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.data_utils import (
    load_categories, load_category_groups, load_transactions
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

@st.cache_data(ttl=60)  # Cache for only 60 seconds
def load_all_data():
    """Load and process all financial data with caching"""
    transactions_df = load_transactions()
    categories_df = load_categories()
    groups_df = load_category_groups()
    
    if len(transactions_df) > 0:
        # Merge with categories and groups for enhanced analysis
        if len(categories_df) > 0:
            transactions_df = transactions_df.merge(
                categories_df[['id', 'name', 'group_id', 'emoji', 'category_type']],
                left_on='category_id',
                right_on='id',
                how='left',
                suffixes=('', '_cat')
            )
            
            if len(groups_df) > 0:
                transactions_df = transactions_df.merge(
                    groups_df[['id', 'name', 'color', 'emoji']],
                    left_on='group_id',
                    right_on='id',
                    how='left',
                    suffixes=('', '_group')
                )
    
    return transactions_df, categories_df, groups_df

def calculate_kpis(df, start_date, end_date):
    """Calculate comprehensive key performance indicators"""
    filtered_df = df[(df['date'] >= pd.to_datetime(start_date)) & 
                     (df['date'] <= pd.to_datetime(end_date))]
    
    total_income = filtered_df[filtered_df['amount'] > 0]['amount'].sum()
    total_expenses = abs(filtered_df[filtered_df['amount'] < 0]['amount'].sum())
    net_balance = total_income - total_expenses
    
    # Previous period comparison
    period_days = (end_date - start_date).days
    prev_start = start_date - timedelta(days=period_days)
    prev_end = start_date
    
    prev_df = df[(df['date'] >= pd.to_datetime(prev_start)) & 
                 (df['date'] < pd.to_datetime(prev_end))]
    prev_expenses = abs(prev_df[prev_df['amount'] < 0]['amount'].sum())
    prev_income = prev_df[prev_df['amount'] > 0]['amount'].sum()
    
    expense_change = ((total_expenses - prev_expenses) / prev_expenses * 100) if prev_expenses > 0 else 0
    income_change = ((total_income - prev_income) / prev_income * 100) if prev_income > 0 else 0
    
    # Additional metrics
    avg_daily_expense = total_expenses / (period_days + 1) if period_days >= 0 else 0
    savings_rate = ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0
    
    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_balance': net_balance,
        'expense_change': expense_change,
        'income_change': income_change,
        'avg_daily_expense': avg_daily_expense,
        'savings_rate': savings_rate,
        'transaction_count': len(filtered_df)
    }

def create_time_series_chart(df):
    """Create comprehensive time series chart for cash flow"""
    daily_flow = df.groupby(df['date'].dt.date)['amount'].sum().reset_index()
    daily_flow['cumulative'] = daily_flow['amount'].cumsum()
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Daily Cash Flow', 'Cumulative Balance'),
        vertical_spacing=0.1,
        row_heights=[0.6, 0.4]
    )
    
    # Daily cash flow with color coding
    colors = ['#ff4444' if x < 0 else '#44ff44' for x in daily_flow['amount']]
    fig.add_trace(
        go.Bar(
            x=daily_flow['date'],
            y=daily_flow['amount'],
            name='Daily Flow',
            marker_color=colors,
            opacity=0.7,
            hovertemplate='<b>%{x}</b><br>Amount: $%{y:,.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Cumulative balance
    fig.add_trace(
        go.Scatter(
            x=daily_flow['date'],
            y=daily_flow['cumulative'],
            name='Cumulative Balance',
            line=dict(color='#2E86AB', width=3),
            fill='tonexty',
            fillcolor='rgba(46, 134, 171, 0.1)',
            hovertemplate='<b>%{x}</b><br>Balance: $%{y:,.2f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        title_text="💰 Cash Flow Analysis",
        title_x=0.5
    )
    
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Amount ($)", row=1, col=1)
    fig.update_yaxes(title_text="Balance ($)", row=2, col=1)
    
    return fig

def create_enhanced_category_chart(df):
    """Create enhanced category spending breakdown with groups"""
    expenses_df = df[df['amount'] < 0].copy()
    expenses_df['amount'] = abs(expenses_df['amount'])
    
    if len(expenses_df) == 0:
        return go.Figure().add_annotation(text="No expense data available", 
                                        xref="paper", yref="paper", x=0.5, y=0.5)
    
    # Use category names if available, otherwise use 'Other'
    category_col = 'name_cat' if 'name_cat' in expenses_df.columns else 'category'
    if category_col not in expenses_df.columns:
        expenses_df[category_col] = 'Uncategorized'
    
    category_spending = expenses_df.groupby(category_col)['amount'].sum().reset_index()
    category_spending = category_spending.sort_values('amount', ascending=False)
    
    # Create donut chart
    fig = px.pie(
        category_spending,
        values='amount',
        names=category_col,
        title='💳 Spending by Category',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Amount: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        height=400,
        title_x=0.5,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01)
    )
    
    return fig

def create_monthly_trend_chart(df, current_start_date, current_end_date):
    """Create enhanced monthly spending trend with current period highlighted"""
    df_monthly = df.copy()
    df_monthly['month'] = df_monthly['date'].dt.to_period('M')
    
    monthly_summary = df_monthly.groupby('month').agg({
        'amount': lambda x: (x[x > 0].sum(), abs(x[x < 0].sum()), x.sum())
    }).reset_index()
    
    monthly_summary[['income', 'expenses', 'net']] = pd.DataFrame(
        monthly_summary['amount'].tolist(), 
        index=monthly_summary.index
    )
    monthly_summary['month_str'] = monthly_summary['month'].astype(str)
    
    # Determine current period for highlighting
    current_period = pd.Period(current_start_date, 'M')
    current_month_str = str(current_period)
    
    fig = go.Figure()
    
    # Add income bars
    fig.add_trace(go.Bar(
        x=monthly_summary['month_str'],
        y=monthly_summary['income'],
        name='Income',
        marker_color=['#90EE90' if month == current_month_str else '#32CD32' 
                     for month in monthly_summary['month_str']],
        opacity=0.8,
        hovertemplate='<b>%{x}</b><br>Income: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add expense bars
    fig.add_trace(go.Bar(
        x=monthly_summary['month_str'],
        y=monthly_summary['expenses'],
        name='Expenses',
        marker_color=['#FFB6C1' if month == current_month_str else '#FF6347' 
                     for month in monthly_summary['month_str']],
        opacity=0.8,
        hovertemplate='<b>%{x}</b><br>Expenses: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add net line
    fig.add_trace(go.Scatter(
        x=monthly_summary['month_str'],
        y=monthly_summary['net'],
        mode='lines+markers',
        name='Net Flow',
        line=dict(color='#2E86AB', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{x}</b><br>Net: $%{y:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'📊 Monthly Trend (Current: {current_month_str})',
        xaxis_title='Month',
        yaxis_title='Amount ($)',
        barmode='group',
        height=400,
        hovermode='x unified',
        title_x=0.5
    )
    
    return fig

def create_category_group_chart(df):
    """Create spending by category group chart"""
    if 'name_group' not in df.columns:
        return None
    
    expenses_df = df[df['amount'] < 0].copy()
    expenses_df['amount'] = abs(expenses_df['amount'])
    
    group_spending = expenses_df.groupby('name_group')['amount'].sum().sort_values(ascending=True)
    
    if len(group_spending) == 0:
        return None
    
    fig = px.bar(
        x=group_spending.values,
        y=group_spending.index,
        orientation='h',
        title="📊 Expenses by Group",
        labels={'x': 'Amount ($)', 'y': 'Category Group'}
    )
    
    fig.update_layout(
        height=300,
        title_x=0.5,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    fig.update_traces(
        hovertemplate='<b>%{y}</b><br>Amount: $%{x:,.2f}<extra></extra>'
    )
    
    return fig

def show():
    st.title("💰 Personal Finance Dashboard")
    st.markdown("Track your expenses, analyze spending patterns, and manage your finances effectively.")
    
    # Add refresh button in header
    col_title, col_refresh = st.columns([4, 1])
    with col_refresh:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    # Load data
    transactions_df, categories_df, groups_df = load_all_data()
    
    if len(transactions_df) == 0:
        st.warning("No transaction data available.")
        return
    
    # Sidebar filters
    st.sidebar.header("🔧 Filters & Navigation")
    
    # Month Navigator - Primary Time Control
    st.sidebar.subheader("📅 Time Navigator")
    
    # Get available months
    transactions_df['year_month'] = transactions_df['date'].dt.to_period('M')
    available_months = sorted(transactions_df['year_month'].unique(), reverse=True)
    available_month_strings = [str(month) for month in available_months]
    
    # Navigation method selector
    nav_method = st.sidebar.radio(
        "Navigation Style:",
        ["Month Navigator", "Custom Date Range"],
        index=0
    )
    
    if nav_method == "Month Navigator" and available_month_strings:
        # Month navigation buttons
        col1, col2, col3 = st.sidebar.columns([1, 2, 1])
        
        # Month selector dropdown
        selected_month_str = st.sidebar.selectbox(
            "Select Month:",
            options=available_month_strings,
            index=0,
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
                    st.rerun()
        
        with quick_col2:
            if st.button("Last Month"):
                last_period = pd.Period.now('M') - 1
                if str(last_period) in available_month_strings:
                    st.session_state.month_selector = str(last_period)
                    st.rerun()
    
    else:  # Custom Date Range
        min_date = transactions_df['date'].min().date()
        max_date = transactions_df['date'].max().date()
        
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
    
    # Category filter
    if 'name_cat' in transactions_df.columns:
        categories = transactions_df['name_cat'].dropna().unique().tolist()
        selected_categories = st.sidebar.multiselect(
            "Select Categories",
            options=categories,
            default=categories
        )
        filtered_df = transactions_df[
            transactions_df['name_cat'].isin(selected_categories) | 
            transactions_df['name_cat'].isna()
        ]
    else:
        filtered_df = transactions_df
    
    # Apply date filter
    filtered_df = filtered_df[
        (filtered_df['date'] >= pd.to_datetime(start_date)) &
        (filtered_df['date'] <= pd.to_datetime(end_date))
    ]
    
    # Debug info (optional)
    if st.sidebar.checkbox("Show Debug Info"):
        st.sidebar.write("**Filtering Debug:**")
        st.sidebar.write(f"Original data: {len(transactions_df)} rows")
        st.sidebar.write(f"After filters: {len(filtered_df)} rows")
        st.sidebar.write(f"Selected period: {start_date} to {end_date}")
        
        if len(filtered_df) > 0:
            filtered_months = filtered_df['date'].dt.strftime('%b %Y').value_counts()
            st.sidebar.write("**Filtered data months:**")
            for month, count in filtered_months.items():
                st.sidebar.write(f"- {month}: {count}")
    
    # Calculate comprehensive KPIs
    kpis = calculate_kpis(filtered_df, start_date, end_date)
    
    # Enhanced KPI Display
    st.markdown("---")
    st.subheader("📈 Financial Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💚 Total Income",
            value=f"${kpis['total_income']:,.2f}",
            delta=f"{kpis['income_change']:.1f}%" if kpis['income_change'] != 0 else None
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
        st.metric(
            label="📊 Avg Daily Spend",
            value=f"${kpis['avg_daily_expense']:.2f}",
            delta=None
        )
    
    # Additional KPIs row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💹 Savings Rate",
            value=f"{kpis['savings_rate']:.1f}%"
        )
    
    with col2:
        st.metric(
            label="📝 Transactions",
            value=f"{kpis['transaction_count']}"
        )
    
    with col3:
        categorized_count = len(filtered_df[filtered_df['category_id'].notna()])
        categorization_rate = (categorized_count / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
        st.metric(
            label="🏷️ Categorized",
            value=f"{categorization_rate:.1f}%"
        )
    
    with col4:
        period_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1
        st.metric(
            label="📅 Days in Period",
            value=f"{period_days}"
        )
    
    # Enhanced Charts Section
    st.markdown("---")
    
    # Main time series chart
    st.plotly_chart(create_time_series_chart(filtered_df), use_container_width=True)
    
    # Category analysis row
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.plotly_chart(create_enhanced_category_chart(filtered_df), use_container_width=True)
    
    with col2:
        group_chart = create_category_group_chart(filtered_df)
        if group_chart:
            st.plotly_chart(group_chart, use_container_width=True)
        else:
            st.info("📝 Category groups not available")
    
    # Monthly trend
    st.plotly_chart(create_monthly_trend_chart(transactions_df, start_date, end_date), use_container_width=True)
    
    # Month-over-Month comparison (enhanced)
    if nav_method == "Month Navigator" and len(available_months) > 1:
        st.markdown("---")
        st.subheader("📊 Month-over-Month Analysis")
        
        current_period = pd.Period(selected_month_str)
        prev_period = current_period - 1
        
        if str(prev_period) in available_month_strings:
            # Current month data
            current_data = transactions_df[transactions_df['year_month'] == current_period]
            current_expenses = abs(current_data[current_data['amount'] < 0]['amount'].sum())
            current_income = current_data[current_data['amount'] > 0]['amount'].sum()
            
            # Previous month data  
            prev_data = transactions_df[transactions_df['year_month'] == prev_period]
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
    
    # Enhanced Top Transactions Section
    st.markdown("---")
    st.subheader("💰 Top Transactions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🔴 Largest Expenses**")
        largest_expenses = filtered_df[filtered_df['amount'] < 0].nsmallest(5, 'amount')
        
        for _, row in largest_expenses.iterrows():
            category_name = row.get('name_cat', 'Uncategorized')
            emoji = row.get('emoji', '💳') if pd.notna(row.get('emoji', '')) else '💳'
            st.write(f"{emoji} **${abs(row['amount']):,.2f}** - {row['description'][:40]}...")
            st.caption(f"{category_name} • {row['date'].strftime('%Y-%m-%d')}")
    
    with col2:
        st.write("**🟢 Largest Income**")
        largest_income = filtered_df[filtered_df['amount'] > 0].nlargest(5, 'amount')
        
        if len(largest_income) > 0:
            for _, row in largest_income.iterrows():
                category_name = row.get('name_cat', 'Uncategorized')
                emoji = row.get('emoji', '💰') if pd.notna(row.get('emoji', '')) else '💰'
                st.write(f"{emoji} **${row['amount']:,.2f}** - {row['description'][:40]}...")
                st.caption(f"{category_name} • {row['date'].strftime('%Y-%m-%d')}")
        else:
            st.info("No income transactions in this period")
    
    # Recent transactions table (enhanced)
    st.markdown("---")
    st.subheader("🕒 Recent Transactions")
    
    recent_df = filtered_df.sort_values('date', ascending=False).head(15)
    
    # Prepare enhanced display data
    display_data = []
    for _, row in recent_df.iterrows():
        category_name = row.get('name_cat', 'Uncategorized')
        emoji = row.get('emoji', '📁') if pd.notna(row.get('emoji', '')) else '📁'
        category_display = f"{emoji} {category_name}" if category_name != 'Uncategorized' else 'Uncategorized'
        
        # Color coding for amount
        amount_str = f"${row['amount']:,.2f}"
        if row['amount'] < 0:
            amount_str = f"-${abs(row['amount']):,.2f}"
        
        display_data.append({
            'Date': row['date'].strftime('%Y-%m-%d'),
            'Description': row['description'][:60] + ('...' if len(row['description']) > 60 else ''),
            'Category': category_display,
            'Amount': amount_str
        })
    
    if display_data:
        st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)
    
    # Summary Statistics (enhanced)
    st.markdown("---")
    st.subheader("📈 Detailed Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Period Information:**")
        st.write(f"• **Date Range:** {start_date} to {end_date}")
        st.write(f"• **Total Transactions:** {len(filtered_df)}")
        st.write(f"• **Days in Period:** {period_days}")
        
        if len(filtered_df) > 0:
            st.write(f"• **Transactions per Day:** {len(filtered_df) / period_days:.1f}")
    
    with col2:
        st.write("**Expense Analysis:**")
        if len(filtered_df[filtered_df['amount'] < 0]) > 0:
            expenses = filtered_df[filtered_df['amount'] < 0]['amount']
            st.write(f"• **Largest Expense:** ${abs(expenses.min()):,.2f}")
            st.write(f"• **Average Expense:** ${abs(expenses.mean()):,.2f}")
            st.write(f"• **Median Expense:** ${abs(expenses.median()):,.2f}")
            st.write(f"• **Total Expense Days:** {expenses.count()}")
    
    with col3:
        st.write("**Income Analysis:**")
        if len(filtered_df[filtered_df['amount'] > 0]) > 0:
            income = filtered_df[filtered_df['amount'] > 0]['amount']
            st.write(f"• **Largest Income:** ${income.max():,.2f}")
            st.write(f"• **Average Income:** ${income.mean():,.2f}")
            st.write(f"• **Median Income:** ${income.median():,.2f}")
            st.write(f"• **Total Income Days:** {income.count()}")
        else:
            st.info("No income transactions in this period")
    
    # Quick Actions (enhanced)
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📋 Categorize Transactions", use_container_width=True):
            st.switch_page("pages/categorize_transactions.py")
    
    with col2:
        if st.button("📂 Manage Categories", use_container_width=True):
            st.switch_page("pages/manage_categories.py")
    
    with col3:
        if st.button("📊 Advanced Analytics", use_container_width=True):
            st.info("Advanced analytics coming soon!")
    
    with col4:
        uncategorized_count = len(transactions_df[transactions_df['category_id'].isna()])
        if st.button(f"🏷️ {uncategorized_count} Uncategorized", use_container_width=True):
            st.switch_page("pages/categorize_transactions.py")