import os
import pandas as pd
import logging
from datetime import datetime

# === Paths ===
BASE_DIR = "data"
RAW_DIR = os.path.join(BASE_DIR, "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
METADATA_DIR = os.path.join(BASE_DIR, "metadata")
LOG_FILE = os.path.join(BASE_DIR, "logs/etl.log")

# === Configure logging ===
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)

# === Load metadata ===
accounts = pd.read_csv(os.path.join(METADATA_DIR, "accounts.csv"))
categories = pd.read_csv(os.path.join(METADATA_DIR, "categories.csv"))
category_groups = pd.read_csv(os.path.join(METADATA_DIR, "category_groups.csv"))
presets = pd.read_csv(os.path.join(METADATA_DIR, "presets.csv"))


def update_with_dedup(new_df, out_file, date_col="date"):
    """Drop overlapping date ranges in existing processed file, then append new data."""
    if date_col not in new_df.columns:
        logging.error(f"'{date_col}' column not found in new_df - skipping file: {out_file}")
        return None

    new_df[date_col] = pd.to_datetime(new_df[date_col], errors="coerce")
    min_date, max_date = new_df[date_col].min(), new_df[date_col].max()
    
    # print(new_df.head())
    # print(min_date, max_date)
    # print(new_df.dtypes)

    if pd.isna(min_date) or pd.isna(max_date):
        logging.warning("No valid dates found in new data - skipping deduplication.")
        return None

    if os.path.exists(out_file):
        existing = pd.read_csv(out_file)
        if not existing.empty and date_col in existing.columns:
            existing[date_col] = pd.to_datetime(existing[date_col], errors="coerce")
            mask = (existing[date_col] >= min_date) & (existing[date_col] <= max_date)
            existing = existing.loc[~mask]
            combined = pd.concat([existing, new_df], ignore_index=True)
        else:
            combined = new_df
    else:
        combined = new_df

    combined = combined.sort_values(by=date_col).reset_index(drop=True)
    combined.to_csv(out_file, index=False)

    logging.info(
        f"Updated {out_file} with {len(new_df)} new rows → {len(combined)} total."
    )
    return combined



def load_and_transform(account_id: str):
    """ETL pipeline with deduplication for one account."""
    try:
        account = accounts[accounts["number"] == int(account_id)]
    except ValueError:
        logging.error(f"Invalid account id: {account_id}")
        return None

    if account.empty:
        logging.warning(f"Account {account_id} not found in accounts.csv")
        return None
    account = account.iloc[0]
    logging.info(f"Processing account {account_id} ({account['name']})")

    # Preset (optional)
    preset = None
    if "default_import_preset_id" in account and pd.notna(
        account["default_import_preset_id"]
    ):
        preset = presets[presets["id"] == account["default_import_preset_id"]]
        preset = preset.iloc[0] if not preset.empty else None

    # Raw files
    account_raw_dir = os.path.join(RAW_DIR, account_id)
    if not os.path.exists(account_raw_dir):
        logging.warning(f"No raw directory found for account {account_id}")
        return None

    all_files = [
        os.path.join(account_raw_dir, f)
        for f in os.listdir(account_raw_dir)
        if f.endswith(".csv")
    ]
    if not all_files:
        logging.warning(f"No raw files found for account {account_id}")
        return None

    dfs = []
    for f in all_files:
        try:
            df = pd.read_csv(f)
        except Exception as e:
            logging.error(f"Failed to read {f} for account {account_id}: {e}")
            continue

        if df.empty:
            logging.info(f"Skipping empty file {f} for account {account_id}")
            continue

        # --- Transform ---
        # print(preset)
        if preset is not None and "date_column" in preset:
            date_col = preset["date_column"]
            fmt = preset.get("date_format")
            print(f"Using preset {preset.id} date column '{date_col}' with format '{fmt}'")
            print("before date parsing \n", df[date_col].head())
            try:
                if pd.notna(fmt):
                    df[date_col] = pd.to_datetime(df[date_col], format=fmt, errors="coerce")
                else:
                    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            except Exception as e:
                logging.warning(f"Date parsing failed for {f}: {e}")
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        elif "date" in df.columns:
            date_col = "date"
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        else:
            logging.error(f"No date preset column found for account {account_id}")
            # date_col = "date"
            continue
        # print(date_col)
        print("after date parsing \n", df[date_col].head())
        
        # Simple category join
        if "category" in df.columns:
            df = df.merge(
                categories[["id", "name", "group_id"]],
                left_on="category",
                right_on="name",
                how="left",
            )
            df = df.merge(
                category_groups[["id", "name"]],
                left_on="group_id",
                right_on="id",
                how="left",
                suffixes=("_category", "_group"),
            )

        df["account_id"] = account.id
        dfs.append(df)

    if not dfs:
        logging.info(f"No usable data found for account {account_id}")
        return None

    new_df = pd.concat(dfs, ignore_index=True)

    # --- Load (with deduplication) ---
    out_file = os.path.join(PROCESSED_DIR, f"{account_id}_transactions.csv")
    final_df = update_with_dedup(new_df, out_file, date_col=date_col)

    if final_df is not None:
        logging.info(
            f"Account {account_id} ({account['name']}) processed successfully. Rows: {len(final_df)}"
        )
        return final_df

    return None


if __name__ == "__main__":
    logging.info("=" * 100)
    logging.info("ETL process started.")
    logging.info("=" * 100)
    for acc_dir in os.listdir(RAW_DIR):
        if os.path.isdir(os.path.join(RAW_DIR, acc_dir)):
            load_and_transform(acc_dir)
