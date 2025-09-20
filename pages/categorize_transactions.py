import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from utils.data_utils import (
    load_categories, load_category_groups, load_transactions, 
    save_transactions, get_category_display_name, load_accounts
)

def load_accounts():
    """Load accounts from CSV"""
    accounts_path = "./data/metadata/accounts.csv"
    
    try:
        if os.path.exists(accounts_path):
            df = pd.read_csv(accounts_path)
            # Filter active accounts
            df = df[df.get('is_active', True) == True]
            return df
        else:
            # Create sample accounts if file doesn't exist
            return pd.DataFrame({
                'id': [16, 17, 18, 19, 20, 21, 22],
                'name': ['Capital 7729', 'Capital 5440', 'Capital 2823', 'Capital 2836', 'Capital 9891', 'Capital 5584', 'Capital 0244'],
                'number': ['7729', '5440', '2823', '2836', '9891', '5584', '0244'],
                'account_type': ['CHECKING', 'CHECKING', 'CHECKING', 'SAVINGS', 'CREDIT_CARD', 'CREDIT_CARD', 'SAVINGS'],
                'is_active': [True] * 7
            })
    except Exception as e:
        st.error(f"Error loading accounts: {str(e)}")
        return pd.DataFrame()

def show():
    st.header("📋 Categorize Transactions")
    
    # Load data
    categories_df = load_categories()
    groups_df = load_category_groups()
    transactions_df = load_transactions()
    accounts_df = load_accounts()
    
    # Create account lookup for displaying account numbers
    account_lookup = {}
    if len(accounts_df) > 0:
        account_lookup = accounts_df.set_index('id')['number'].to_dict()
    
    # Overall stats (fixed based on all transactions)
    if len(transactions_df) > 0:
        total_all = len(transactions_df)
        uncategorized_all = len(transactions_df[transactions_df['category_id'].isna()])
        categorized_all = total_all - uncategorized_all
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Transactions", total_all)
        col2.metric("Uncategorized", uncategorized_all)
        col3.metric("Categorized", categorized_all)
        
        if total_all > 0:
            overall_progress = categorized_all / total_all
            st.progress(overall_progress, text=f"Overall Progress: {overall_progress:.1%}")
        
        st.markdown("---")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_filter = st.selectbox(
            "Show:",
            ["Uncategorized Only", "All", "Categorized Only"],
            index=0  # Default to uncategorized
        )
    
    with col2:
        days_back = st.selectbox(
            "Time Period:",
            [7, 14, 30, 60, 90],
            index=2  # Default to 30 days
        )
    
    with col3:
        search_term = st.text_input("Search Description:", placeholder="e.g. WALMART")
    
    # Filter transactions
    cutoff_date = datetime.now() - timedelta(days=days_back)
    filtered_df = transactions_df[transactions_df['date'] >= cutoff_date].copy()
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['description'].str.contains(search_term, case=False, na=False)
        ]
    
    # Apply categorization filter
    if show_filter == "Uncategorized Only":
        filtered_df = filtered_df[filtered_df['category_id'].isna()]
    elif show_filter == "Categorized Only":
        filtered_df = filtered_df[filtered_df['category_id'].notna()]
    
    # Filtered results info
    st.info(f"Showing {len(filtered_df)} transactions from the last {days_back} days")
    
    # Transaction categorization
    if len(filtered_df) > 0:
        st.markdown("---")
        
        # Categories and groups lookup for display
        categories_lookup = categories_df.set_index('id')[['name', 'emoji', 'category_type', 'group_id']].to_dict('index')
        groups_lookup = groups_df.set_index('id')[['name', 'emoji']].to_dict('index')
        
        # Sort by date (newest first)
        filtered_df = filtered_df.sort_values('date', ascending=False)
        
        # Individual transaction categorization
        for idx, row in filtered_df.head(15).iterrows():  # Show first 15
            is_categorized = not pd.isna(row['category_id'])
            
            # Determine card class based on amount and categorization status
            if not is_categorized:
                card_class = "uncategorized-row"
            elif row['amount'] > 0:
                card_class = "positive-amount-row"
            elif row['amount'] < 0:
                card_class = "negative-amount-row"
            else:
                card_class = "categorized-row"
            
            # Transaction display
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                current_category = "Uncategorized"
                current_group = ""
                if is_categorized and row['category_id'] in categories_lookup:
                    cat_info = categories_lookup[row['category_id']]
                    emoji = cat_info.get('emoji', '📁') if pd.notna(cat_info.get('emoji', '')) else '📁'
                    current_category = f"{emoji} {cat_info['name']}" if emoji != '📁' else cat_info['name']
                    
                    # Get group info
                    if cat_info['group_id'] in groups_lookup:
                        group_info = groups_lookup[cat_info['group_id']]
                        group_emoji = group_info.get('emoji', '📂') if pd.notna(group_info.get('emoji', '')) else '📂'
                        current_group = f" ({group_emoji} {group_info['name']})"
                
                # Format amount with proper sign
                amount_str = f"${row['amount']:,.2f}" if row['amount'] >= 0 else f"-${abs(row['amount']):,.2f}"
                amount_color = "green" if row['amount'] > 0 else "red" if row['amount'] < 0 else "gray"
                
                # Get account number from lookup, fallback to account_id if not found
                account_display = account_lookup.get(row.get('account_id'), row.get('account_id', 'Unknown'))
                
                st.markdown(f"""
                <div class="{card_class}">
                    <strong>{row['description']}</strong><br>
                    <small>{row['date'].strftime('%Y-%m-%d')} | <span style="color: {amount_color}; font-weight: bold;">{amount_str}</span> | Account: {account_display}</small><br>
                    <em>{current_category}{current_group}</em>
                </div>
                """, unsafe_allow_html=True)
            
            # Cascading selection: Type -> Group -> Category
            with col2:
                # Step 1: Category type selector
                category_types = ['', 'expense', 'income', 'transfer']
                current_type = ''
                if is_categorized and row['category_id'] in categories_lookup:
                    current_type = categories_lookup[row['category_id']].get('category_type', '')
                
                selected_type = st.selectbox(
                    "Type",
                    options=category_types,
                    index=category_types.index(current_type) if current_type in category_types else 0,
                    key=f"type_{idx}",
                    label_visibility="collapsed",
                    placeholder="Select type..."
                )
            
            with col3:
                # Step 2: Group selector (filtered by type)
                if selected_type:
                    # Get categories of selected type and their unique groups
                    type_categories = categories_df[categories_df['category_type'] == selected_type]
                    type_group_ids = type_categories['group_id'].unique()
                    type_groups = groups_df[groups_df['id'].isin(type_group_ids)]
                    
                    group_options = [None] + type_groups['id'].tolist()
                    
                    current_group_idx = 0
                    if is_categorized and row['category_id'] in categories_lookup:
                        current_group_id = categories_lookup[row['category_id']].get('group_id')
                        if current_group_id in group_options:
                            current_group_idx = group_options.index(current_group_id)
                    
                    selected_group = st.selectbox(
                        "Group",
                        options=group_options,
                        index=current_group_idx,
                        format_func=lambda x: "Select..." if x is None else f"{groups_df[groups_df['id']==x].iloc[0].get('emoji', '📂')} {groups_df[groups_df['id']==x].iloc[0]['name']}",
                        key=f"group_{idx}",
                        label_visibility="collapsed"
                    )
                else:
                    selected_group = None
                    st.selectbox(
                        "Group",
                        options=[None],
                        format_func=lambda x: "Choose type first",
                        key=f"group_disabled_{idx}",
                        disabled=True,
                        label_visibility="collapsed"
                    )
            
            with col4:
                # Step 3: Category selector (filtered by type and group)
                if selected_type and selected_group:
                    group_categories = categories_df[
                        (categories_df['category_type'] == selected_type) & 
                        (categories_df['group_id'] == selected_group)
                    ]
                    category_options = [None] + group_categories['id'].tolist()
                    
                    current_cat_idx = 0
                    if is_categorized and row['category_id'] in category_options:
                        current_cat_idx = category_options.index(row['category_id'])
                    
                    selected_category = st.selectbox(
                        "Category",
                        options=category_options,
                        index=current_cat_idx,
                        format_func=lambda x: "Select..." if x is None else get_category_display_name(categories_df[categories_df['id']==x].iloc[0]),
                        key=f"cat_{idx}",
                        label_visibility="collapsed"
                    )
                else:
                    selected_category = None
                    placeholder_text = "Choose group first" if selected_type else "Choose type first"
                    st.selectbox(
                        "Category",
                        options=[None],
                        format_func=lambda x: placeholder_text,
                        key=f"cat_disabled_{idx}",
                        disabled=True,
                        label_visibility="collapsed"
                    )
            
            with col5:
                # Action buttons
                if selected_category:
                    if st.button("💾", key=f"save_{idx}", help="Save category"):
                        # Update the original dataframe
                        transactions_df.loc[transactions_df['id'] == row['id'], 'category_id'] = selected_category
                        if save_transactions(transactions_df):
                            st.success("Saved!", icon="✅")
                            st.rerun()
                
                # Clear button (only show if categorized)
                if is_categorized:
                    if st.button("🗑️", key=f"clear_{idx}", help="Clear category"):
                        transactions_df.loc[transactions_df['id'] == row['id'], 'category_id'] = np.nan
                        if save_transactions(transactions_df):
                            st.success("Cleared!", icon="✅")
                            st.rerun()
            
            st.markdown("---")
        
    else:
        st.info("No transactions found matching the current filters.")