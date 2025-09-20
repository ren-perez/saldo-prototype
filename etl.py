import os
import pandas as pd
import logging
import json
import hashlib
from datetime import datetime
from typing import Dict, Optional, List

# === Paths ===
BASE_DIR = "data"
RAW_DIR = os.path.join(BASE_DIR, "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
METADATA_DIR = os.path.join(BASE_DIR, "metadata")
LOG_FILE = os.path.join(BASE_DIR, "logs/etl.log")

# Canonical transactions file
TRANSACTIONS_FILE = os.path.join(PROCESSED_DIR, "transactions.csv")

# === Configure logging ===
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)

# === Canonical Schema ===
CANONICAL_COLUMNS = [
    'id', 'date', 'description', 'amount', 'created_at', 'updated_at', 
    'account_id', 'category_id', 'transaction_type'
]

# === Load metadata ===
def load_metadata():
    """Load all metadata tables"""
    try:
        accounts = pd.read_csv(os.path.join(METADATA_DIR, "accounts.csv"))
        categories = pd.read_csv(os.path.join(METADATA_DIR, "categories.csv"))
        category_groups = pd.read_csv(os.path.join(METADATA_DIR, "category_groups.csv"))
        presets = pd.read_csv(os.path.join(METADATA_DIR, "presets.csv"))
        return accounts, categories, category_groups, presets
    except Exception as e:
        logging.error(f"Failed to load metadata: {e}")
        raise


def generate_transaction_id(account_id: str, date: str, amount: float, description: str) -> str:
    """Generate deterministic transaction ID"""
    id_string = f"{account_id}_{date}_{amount}_{description}"
    return hashlib.md5(id_string.encode()).hexdigest()[:12]


def parse_amount_processing(amount_processing_str: str) -> Dict:
    """Parse the JSON amount_processing field from preset"""
    try:
        if pd.isna(amount_processing_str) or not amount_processing_str:
            return {}
        return json.loads(amount_processing_str)
    except json.JSONDecodeError as e:
        logging.warning(f"Failed to parse amount_processing: {e}")
        return {}


def parse_amount_columns(amount_columns_str: str) -> List[str]:
    """Parse the JSON amount_columns field from preset"""
    try:
        if pd.isna(amount_columns_str) or not amount_columns_str:
            return []
        return json.loads(amount_columns_str)
    except json.JSONDecodeError as e:
        logging.warning(f"Failed to parse amount_columns: {e}")
        return []


def process_amount_with_preset(df: pd.DataFrame, preset: pd.Series) -> pd.DataFrame:
    """Process amount based on preset configuration"""
    df = df.copy()
    
    amount_columns = parse_amount_columns(preset.get('amount_columns', '[]'))
    amount_processing = parse_amount_processing(preset.get('amount_processing', '{}'))
    
    if not amount_columns:
        logging.warning("No amount_columns found in preset")
        return df
    
    # Handle different amount processing types
    if 'debit_column' in amount_processing and 'credit_column' in amount_processing:
        # Separate debit/credit columns (e.g., Capital One Credit Card)
        debit_col = amount_processing['debit_column']
        credit_col = amount_processing['credit_column']
        debit_mult = amount_processing.get('debit_multiplier', 1)
        credit_mult = amount_processing.get('credit_multiplier', -1)
        
        # Convert to numeric, treating empty/null as 0
        df[debit_col] = pd.to_numeric(df[debit_col], errors='coerce').fillna(0)
        df[credit_col] = pd.to_numeric(df[credit_col], errors='coerce').fillna(0)
        
        df['amount'] = (df[debit_col] * debit_mult) + (df[credit_col] * credit_mult)
        
    elif 'amount_column' in amount_processing:
        # Single amount column with transaction type (e.g., Capital One Checking)
        amount_col = amount_processing['amount_column']
        type_col = amount_processing.get('transaction_type_column')
        debit_values = amount_processing.get('debit_values', [])
        credit_values = amount_processing.get('credit_values', [])
        
        df['amount'] = pd.to_numeric(df[amount_col], errors='coerce').fillna(0)
        
        # Apply sign based on transaction type
        if type_col and type_col in df.columns:
            # Debit = negative, Credit = positive (or use multiplier)
            multiplier = amount_processing.get('amount_multiplier', 1)
            mask_debit = df[type_col].isin(debit_values)
            df.loc[mask_debit, 'amount'] = df.loc[mask_debit, 'amount'] * -1 * multiplier
            df.loc[~mask_debit, 'amount'] = df.loc[~mask_debit, 'amount'] * multiplier
    
    else:
        # Simple case - just use first amount column
        amount_col = amount_columns[0]
        df['amount'] = pd.to_numeric(df[amount_col], errors='coerce').fillna(0)
        
        # Apply multiplier if specified
        multiplier = preset.get('amount_multiplier', 1)
        if pd.notna(multiplier):
            df['amount'] = df['amount'] * multiplier
    
    return df


def normalize_to_canonical_schema(df: pd.DataFrame, account_row: pd.Series, preset: Optional[pd.Series], categories: pd.DataFrame) -> pd.DataFrame:
    """Transform raw data to canonical schema"""
    normalized = pd.DataFrame()
    
    # Date parsing
    if preset is not None and 'date_column' in preset and pd.notna(preset['date_column']):
        date_col = preset['date_column']
        date_format = preset.get('date_format')
        
        if date_col in df.columns:
            try:
                if pd.notna(date_format):
                    normalized['date'] = pd.to_datetime(df[date_col], format=date_format, errors='coerce')
                else:
                    normalized['date'] = pd.to_datetime(df[date_col], errors='coerce')
            except Exception as e:
                logging.warning(f"Date parsing failed: {e}")
                normalized['date'] = pd.to_datetime(df[date_col], errors='coerce')
        else:
            logging.error(f"Date column '{date_col}' not found in data")
            return pd.DataFrame()
    else:
        # Fallback to 'date' column
        if 'date' in df.columns:
            normalized['date'] = pd.to_datetime(df['date'], errors='coerce')
        else:
            logging.error("No date column found")
            return pd.DataFrame()
    
    # Description
    if preset is not None and 'description_column' in preset and pd.notna(preset['description_column']):
        desc_col = preset['description_column']
        if desc_col in df.columns:
            normalized['description'] = df[desc_col].astype(str).fillna('')
        else:
            normalized['description'] = ''
    elif 'description' in df.columns:
        normalized['description'] = df['description'].astype(str).fillna('')
    else:
        normalized['description'] = ''
    
    # Amount processing
    if preset is not None:
        df_with_amount = process_amount_with_preset(df, preset)
        normalized['amount'] = df_with_amount['amount']
    else:
        # Fallback amount processing
        if 'amount' in df.columns:
            normalized['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
        else:
            normalized['amount'] = 0
    
    # Transaction type
    if preset is not None and 'transaction_type_column' in preset and pd.notna(preset['transaction_type_column']):
        type_col = preset['transaction_type_column']
        if type_col in df.columns:
            normalized['transaction_type'] = df[type_col].astype(str).fillna('')
        else:
            normalized['transaction_type'] = ''
    elif 'transaction_type' in df.columns:
        normalized['transaction_type'] = df['transaction_type'].astype(str).fillna('')
    else:
        # Infer from amount
        normalized['transaction_type'] = normalized['amount'].apply(
            lambda x: 'debit' if x < 0 else 'credit' if x > 0 else 'zero'
        )
    
    # Account ID
    normalized['account_id'] = account_row['id']
    
    # Category matching
    normalized['category_id'] = None
    if preset is not None and 'category_column' in preset and pd.notna(preset['category_column']):
        cat_col = preset['category_column']
        if cat_col in df.columns:
            # Simple category name matching
            cat_lookup = dict(zip(categories['name'], categories['id']))
            normalized['category_id'] = df[cat_col].map(cat_lookup)
    
    # Timestamps
    now = datetime.now().isoformat()
    normalized['created_at'] = now
    normalized['updated_at'] = now
    
    # Generate IDs
    normalized['id'] = normalized.apply(
        lambda row: generate_transaction_id(
            str(row['account_id']), 
            str(row['date']), 
            float(row['amount']), 
            str(row['description'])
        ), axis=1
    )
    
    # Ensure all canonical columns exist
    for col in CANONICAL_COLUMNS:
        if col not in normalized.columns:
            normalized[col] = None
    
    # Reorder columns to match canonical schema
    normalized = normalized[CANONICAL_COLUMNS]
    
    # Remove rows with invalid dates
    normalized = normalized.dropna(subset=['date'])
    
    return normalized


def delta_load_transactions(new_df: pd.DataFrame, account_id: str, accounts: pd.DataFrame) -> pd.DataFrame:
    """Update canonical transactions.csv with delta load logic"""
    if new_df.empty:
        logging.warning(f"No new data for account {account_id}")
        return pd.DataFrame()
    
    new_df['date'] = pd.to_datetime(new_df['date'])
    min_date, max_date = new_df['date'].min(), new_df['date'].max()
    
    if pd.isna(min_date) or pd.isna(max_date):
        logging.warning(f"No valid dates in new data for account {account_id}")
        return pd.DataFrame()
    
    # Get the account's internal ID from the account number
    account_row = accounts[accounts['number'] == int(account_id)]
    if account_row.empty:
        logging.error(f"Account {account_id} not found in accounts metadata")
        return pd.DataFrame()
    
    account_internal_id = account_row.iloc[0]['id']
    
    # print(f"account_id (number): {account_id}, internal_id: {account_internal_id}, date range: {min_date.date()} to {max_date.date()}")
    
    # Load existing transactions
    if os.path.exists(TRANSACTIONS_FILE):
        existing_df = pd.read_csv(TRANSACTIONS_FILE)
        existing_df['date'] = pd.to_datetime(existing_df['date'])
        
        print(f"existing_df account_ids: {existing_df['account_id'].unique()}")
        
        # Remove overlapping date range for this account
        mask = (
            (existing_df['account_id'] == account_internal_id) & 
            (existing_df['date'] >= min_date) & 
            (existing_df['date'] <= max_date)
        )
        
        overlapping_count = mask.sum()
        if overlapping_count > 0:
            logging.info(f"Removed {overlapping_count} duplicate transactions based on date")
        
        existing_df = existing_df[~mask]
        
        # Combine with new data
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df
    
    # Sort by date and save
    combined_df = combined_df.sort_values(['account_id', 'date']).reset_index(drop=True)
    
    # Ensure directory exists
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    combined_df.to_csv(TRANSACTIONS_FILE, index=False)
    
    logging.info(f"Updated transactions.csv with {len(new_df)} new rows for account {account_id}. Total: {len(combined_df)}")
    
    return combined_df

def process_account(account_id: str, accounts: pd.DataFrame, presets: pd.DataFrame, categories: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Process all raw files for a single account"""
    try:
        account_row = accounts[accounts['number'] == int(account_id)]
    except (ValueError, KeyError):
        logging.error(f"Invalid account_id: {account_id}")
        return None
    
    if account_row.empty:
        logging.warning(f"Account {account_id} not found in accounts metadata")
        return None
    
    account_row = account_row.iloc[0]
    logging.info(f"Processing account {account_id} ({account_row.get('name', 'Unknown')})")
    
    # Get preset
    preset = None
    if 'default_import_preset_id' in account_row and pd.notna(account_row['default_import_preset_id']):
        preset_rows = presets[presets['id'] == account_row['default_import_preset_id']]
        if not preset_rows.empty:
            preset = preset_rows.iloc[0]
            logging.info(f"Using preset: {preset.get('name', preset['id'])}")
    
    # Process raw files
    account_raw_dir = os.path.join(RAW_DIR, str(account_id))
    if not os.path.exists(account_raw_dir):
        logging.warning(f"No raw directory for account {account_id}")
        return None
    
    csv_files = [f for f in os.listdir(account_raw_dir) if f.endswith('.csv')]
    if not csv_files:
        logging.warning(f"No CSV files found for account {account_id}")
        return None
    
    processed_count = 0
    for filename in csv_files:
        filepath = os.path.join(account_raw_dir, filename)
        try:
            # Load raw data
            if preset is not None:
                delimiter = preset.get('delimiter', ',')
                has_header = preset.get('has_header', True)
                skip_rows = preset.get('skip_rows', 0)
                
                raw_df = pd.read_csv(
                    filepath,
                    delimiter=delimiter,
                    header=0 if has_header else None,
                    skiprows=skip_rows
                )
            else:
                raw_df = pd.read_csv(filepath)
            
            if raw_df.empty:
                logging.info(f"Skipping empty file: {filename}")
                continue
            
            # Normalize to canonical schema
            normalized_df = normalize_to_canonical_schema(raw_df, account_row, preset, categories)
            if not normalized_df.empty:
                # Apply delta load for each file individually
                result_df = delta_load_transactions(normalized_df, account_id, accounts)
                processed_count += len(normalized_df)
                logging.info(f"Processed {len(normalized_df)} transactions from {filename}")
            
        except Exception as e:
            logging.error(f"Failed to process {filename} for account {account_id}: {e}")
            continue
    
    if processed_count == 0:
        logging.info(f"No usable data for account {account_id}")
        return None
    
    # Load final result for return
    result_df = pd.read_csv(TRANSACTIONS_FILE) if os.path.exists(TRANSACTIONS_FILE) else pd.DataFrame()
    
    logging.info(f"Account {account_id} processing complete. Processed {processed_count} transactions.")
    return result_df


def main():
    """Main ETL process"""
    logging.info("=" * 50)
    logging.info("ETL process started")
    logging.info("=" * 50)
    
    try:
        # Load metadata
        accounts, categories, category_groups, presets = load_metadata()
        
        # Process each account directory
        processed_accounts = 0
        for item in os.listdir(RAW_DIR):
            account_dir = os.path.join(RAW_DIR, item)
            if os.path.isdir(account_dir):
                result = process_account(item, accounts, presets, categories)
                if result is not None:
                    processed_accounts += 1
        
        logging.info(f"ETL process completed. Processed {processed_accounts} accounts.")
        
        # Log final stats
        if os.path.exists(TRANSACTIONS_FILE):
            final_df = pd.read_csv(TRANSACTIONS_FILE)
            logging.info(f"Final transactions.csv contains {len(final_df)} total transactions")
            
    except Exception as e:
        logging.error(f"ETL process failed: {e}")
        raise


if __name__ == "__main__":
    main()