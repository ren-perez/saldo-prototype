# Saldo Prototype

## Prototype Checklist

### 1. **Folder Structure**

```
saldo-prototype/
├── .gitignore
├── dashboard.py
├── main.py
├── etl.py
├── README.md
├── utils/
│   ├── __init__.py
│   └── data_utils.py
├── pages/
│   ├── __init__.py           # 👈 add this so imports work
│   ├── dashboard.py          # defines show()
│   ├── categorize_transactions.py
│   └── manage_categories.py
├── data/
│   ├── metadata/
│   │   ├── accounts.csv
│   │   ├── banks.csv
│   │   ├── categories.csv
│   │   ├── category_groups.csv
│   │   └── presets.csv
│   ├── processed/
│   │   └── transactions.csv   # canonical “table” of all transactions
│   └── raw/
│       ├── 0244/
│       ├── 2823/
│       ├── 2836/
│       ├── 5440/
│       ├── 5584/
│       ├── 7729/
│       └── 9891/
```

---

### 2. **Metadata Setup**

* `accounts.csv` → parsing rules per account
  Example:

  ```csv
  account_id,account_name,bank,default_import_preset_id,currency
  1,Chase,Chase,1,USD
  2,Amex,American Express,2,USD
  ```

* `presets.csv` → column mappings for raw files
  Example:

  ```csv
  id,date_column,amount_column,description_column,date_format,delimiter
  1,Date,Amount,Description,%m/%d/%Y,","
  2,Transaction Date,Amount,Details,%Y-%m-%d,";"
  ```

* `categories.csv` → canonical categories
  Example:

  ```csv
  id,name,group_id
  1,Groceries,1
  2,Rent,1
  3,Dining,2
  4,Travel,3
  ```

* `category_groups.csv` → category groupings
  Example:

  ```csv
  id,name
  1,Essentials
  2,Discretionary
  3,Lifestyle
  ```

---

### 3. **ETL Script (`etl.py`)**

* Input: processes all new files under `data/raw/{account_id}/`.
* Steps:

  1. Detect account from folder name.

  2. Load preset via `default_import_preset_id` in `accounts.csv`.

  3. Normalize raw file → canonical schema:

     ```
     id,date,description,amount,created_at,updated_at,account_id,category_id,transaction_type
     ```

     * `id` = deterministic hash of `(account_id, date, amount, description)`.
     * `created_at/updated_at` = UTC timestamps.
     * `transaction_type` = inferred from preset rules (optional).
     * `category_id` = joined from `categories.csv` if matched.

  4. Delta load:

     * Drop existing rows in `transactions.csv` within `[min_date, max_date]` for that `account_id`.
     * Append new rows.

  5. Save back to `processed/transactions.csv`.

---

### 4. **Processed Data**

* Master CSV file: `data/processed/transactions.csv`
  Columns:

  ```
  id,date,description,amount,created_at,updated_at,account_id,category_id,transaction_type
  ```

* This file is the **single source of truth** for the dashboard.

---

### 5. **Streamlit Dashboard (`dashboard.py`)**

* Loads `transactions.csv` + metadata (`accounts.csv`, `categories.csv`, `category_groups.csv`).
* Features:

  * Filter by **account** (multi-select).
  * Filter by **category** (multi-select).
  * Date range filter.
  * KPIs: Total Income, Total Expenses, Net Balance.
  * Visuals:

    * Time series of cash flow.
    * Donut chart of spending by category.

---

### 6. **Workflow (Manual Prototype)**

1. Drop new raw CSV files into `data/raw/{account_id}/`.

2. Run:

   ```bash
   python etl.py
   ```

   → Updates `data/processed/transactions.csv`.

3. Run:

   ```bash
   streamlit run dashboard.py
   ```

   → Dashboard reflects latest processed data.

---

### 7. **Next Step (after prototype)**

* Replace `transactions.csv` with Supabase/Postgres (real DB table).
* Replace manual ETL run with **event-driven job** (e.g., Cloud Run trigger on file upload).
* Replace Streamlit with **Next.js UI** for multi-user experience.

---

✅ With this setup, you have a **real ETL prototype**:

* Raw → Preset Normalization → Canonical Transactions Table.
* Deduplication + delta loads.
* Interactive dashboard for validation.

---

Would you like me to also add an **example schema for `transactions.csv`** (with sample rows) so future you remembers exactly how the normalized file looks?
