import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import streamlit as st

def load_categories():
    """Load categories from CSV"""
    categories_path = "./data/metadata/categories.csv"
    
    try:
        if os.path.exists(categories_path):
            df = pd.read_csv(categories_path)
            # Keep only required columns
            required_cols = ['id', 'name', 'group_id', 'description', 'emoji', 'created_at', 'updated_at', 'is_active', 'category_type']
            available_cols = [col for col in required_cols if col in df.columns]
            df = df[available_cols]
            # Filter active categories
            df = df[df.get('is_active', True) == True]
            return df
        else:
            return create_sample_categories()
    except Exception as e:
        st.error(f"Error loading categories: {str(e)}")
        return create_sample_categories()

def load_category_groups():
    """Load category groups from CSV"""
    groups_path = "./data/metadata/category_groups.csv"
    
    try:
        if os.path.exists(groups_path):
            df = pd.read_csv(groups_path)
            # Keep only required columns
            required_cols = ['id', 'name', 'user_id', 'color', 'emoji', 'created_at', 'updated_at', 'is_active']
            available_cols = [col for col in required_cols if col in df.columns]
            df = df[available_cols]
            # Filter active groups
            df = df[df.get('is_active', True) == True]
            return df
        else:
            return create_sample_groups()
    except Exception as e:
        st.error(f"Error loading category groups: {str(e)}")
        return create_sample_groups()

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
            # Create sample accounts based on the CSV structure you provided
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

def load_transactions():
    """Load transactions from CSV"""
    transactions_path = "data/processed/transactions.csv"
    
    try:
        if os.path.exists(transactions_path):
            df = pd.read_csv(transactions_path)
            df['date'] = pd.to_datetime(df['date'])
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            return df
        else:
            return create_sample_transactions()
    except Exception as e:
        st.error(f"Error loading transactions: {str(e)}")
        return create_sample_transactions()

def save_categories(categories_df):
    """Save categories to CSV"""
    try:
        categories_path = "./data/metadata/categories.csv"
        os.makedirs(os.path.dirname(categories_path), exist_ok=True)
        categories_df.to_csv(categories_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving categories: {str(e)}")
        return False

def save_category_groups(groups_df):
    """Save category groups to CSV"""
    try:
        groups_path = "./data/metadata/category_groups.csv"
        os.makedirs(os.path.dirname(groups_path), exist_ok=True)
        groups_df.to_csv(groups_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving category groups: {str(e)}")
        return False

def save_transactions(transactions_df):
    """Save transactions to CSV"""
    try:
        transactions_path = "data/processed/transactions.csv"
        os.makedirs(os.path.dirname(transactions_path), exist_ok=True)
        transactions_df.to_csv(transactions_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving transactions: {str(e)}")
        return False

def create_sample_categories():
    """Create sample categories for demo"""
    return pd.DataFrame({
        'id': [95, 96, 97, 98, 99, 100, 101, 102],
        'name': ['Honda', 'Gym', 'Rent', 'Withdrawal', 'Leisure', 'Groceries', 'Dining', 'Shopping'],
        'group_id': [52, 51, 41, 42, 48, 41, 48, 48],
        'description': ['Car payments', 'Fitness expenses', 'Housing costs', 'Cash withdrawals', 
                       'Entertainment', 'Food shopping', 'Restaurant meals', 'General shopping'],
        'emoji': ['🚗', '💪', '🏠', '💰', '🎉', '🛒', '🍽️', '🛍️'],
        'category_type': ['expense', 'expense', 'expense', 'transfer', 'expense', 'expense', 'expense', 'expense'],
        'is_active': [True] * 8,
        'created_at': [datetime.now()] * 8,
        'updated_at': [datetime.now()] * 8
    })

def create_sample_groups():
    """Create sample category groups for demo"""
    return pd.DataFrame({
        'id': [41, 42, 48, 51, 52],
        'name': ['Housing', 'Savings - Emergency', 'Entertainment', 'Health & Fitness', 'Transportation'],
        'user_id': [13] * 5,
        'color': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57'],
        'emoji': ['🏠', '💰', '🎉', '💪', '🚗'],
        'is_active': [True] * 5,
        'created_at': [datetime.now()] * 5,
        'updated_at': [datetime.now()] * 5
    })

def create_sample_transactions():
    """Create sample transactions for demo"""
    np.random.seed(42)
    start_date = datetime.now() - timedelta(days=30)
    dates = pd.date_range(start=start_date, end=datetime.now(), freq='D')
    
    descriptions = [
        'HONDA FINANCIAL', 'PLANET FITNESS', 'RENT PAYMENT', 'ATM WITHDRAWAL',
        'NETFLIX', 'WALMART SUPERCENTER', 'STARBUCKS', 'AMAZON.COM',
        'SHELL GAS STATION', 'TARGET', 'UBER EATS', 'GROCERY OUTLET'
    ]
    
    transactions = []
    for i, date in enumerate(dates[:20]):  # Limit for demo
        desc = np.random.choice(descriptions)
        amount = -np.random.uniform(10, 200) if 'PAYMENT' not in desc else np.random.uniform(500, 2000)
        
        transactions.append({
            'id': f"tx_{i}",
            'date': date,
            'description': desc,
            'amount': amount,
            'category_id': np.nan,  # Start uncategorized
            'account_id': np.random.choice([16, 17, 18]),
            'transaction_type': 'Credit' if amount > 0 else 'Debit'
        })
    
    return pd.DataFrame(transactions)

def get_category_display_name(cat_row):
    """Get formatted display name for category"""
    emoji = cat_row.get('emoji', '📁') if pd.notna(cat_row.get('emoji', '')) else '📁'
    name = cat_row['name']
    return f"{emoji} {name}" if emoji and emoji != '📁' else name