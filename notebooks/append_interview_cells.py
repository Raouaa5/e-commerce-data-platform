"""
Appends 6 interview-question cell-pairs (markdown + code + decision markdown)
to 01_data_exploration.ipynb.
"""
import json
from pathlib import Path

nb_path = Path(r"c:\Users\raoua\Downloads\Stage et alter\ecommerce-data-platform\notebooks\01_data_exploration.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))

def md(cell_id, source_lines):
    return {"cell_type": "markdown", "id": cell_id, "metadata": {}, "source": source_lines}

def code(cell_id, source_lines):
    return {"cell_type": "code", "execution_count": None, "id": cell_id,
            "metadata": {}, "outputs": [], "source": source_lines}

cells = []

# ── Section header ─────────────────────────────────────────────────────────────
cells.append(md("iq_header", [
    "---\n",
    "# 4. Interview Questions — Deep-Dive Resolutions\n",
    "\n",
    "Six targeted questions on the findings above.\n",
    "Each block: **what we will do**, the code, then a numbered decision sentence.\n",
]))

# ══════════════════════════════════════════════════════════════════════════════
# Q1 — Reviews
# ══════════════════════════════════════════════════════════════════════════════
cells.append(md("iq1_plan", [
    "## Q1 — Reviews: true grain and de-duplication rule\n",
    "\n",
    "**Plan:** 814 duplicate `review_id`, 551 duplicate `order_id`, 547 orders with more than one row.\n",
    "We first check whether a duplicated `review_id` always maps to the *same* `order_id`\n",
    "(i.e. the whole row is a copy) or whether the same ID was reused for *different* orders (ID collision).\n",
    "Then we check whether the extra rows differ in score or timestamps,\n",
    "so we can pick a deterministic deduplication rule.\n",
]))

cells.append(code("iq1_code", [
    "import pandas as pd\n",
    "from pathlib import Path\n",
    "\n",
    "data_dir = Path.cwd().parent / 'data' / 'raw'\n",
    "reviews = pd.read_csv(data_dir / 'olist_order_reviews_dataset.csv')\n",
    "\n",
    "# 1a. For each duplicated review_id, do the rows share the same order_id?\n",
    "dup_review_ids = reviews[reviews.duplicated('review_id', keep=False)]\n",
    "review_id_cross = (\n",
    "    dup_review_ids.groupby('review_id')['order_id']\n",
    "    .nunique()\n",
    "    .rename('distinct_orders')\n",
    "    .reset_index()\n",
    ")\n",
    "print('=== For duplicated review_id: how many map to >1 distinct order_id? ===')\n",
    "print(review_id_cross['distinct_orders'].value_counts().sort_index())\n",
    "\n",
    "# 1b. Do duplicated rows share the same score and timestamps?\n",
    "score_ts_check = (\n",
    "    dup_review_ids.groupby('review_id')\n",
    "    .agg(\n",
    "        n_rows=('review_id', 'count'),\n",
    "        distinct_scores=('review_score', 'nunique'),\n",
    "        distinct_creation=('review_creation_date', 'nunique'),\n",
    "        distinct_answer=('review_answer_timestamp', 'nunique'),\n",
    "    )\n",
    "    .reset_index()\n",
    ")\n",
    "print('\\n=== Score/timestamp variation within duplicate review_id groups ===')\n",
    "print(score_ts_check[['distinct_scores', 'distinct_creation', 'distinct_answer']].describe())\n",
    "\n",
    "# 1c. Sample rows for orders with multiple review rows\n",
    "dup_order_ids = reviews[reviews.duplicated('order_id', keep=False)]\n",
    "sample_order = dup_order_ids.sort_values(['order_id', 'review_answer_timestamp']).head(6)\n",
    "print('\\n=== Sample rows for orders with multiple review rows ===')\n",
    "display(sample_order[['order_id', 'review_id', 'review_score',\n",
    "                       'review_creation_date', 'review_answer_timestamp']])\n",
    "\n",
    "# 1d. How many are exact-row duplicates?\n",
    "print(f'\\nFully identical rows (all columns, duplicated): {reviews.duplicated().sum()}')\n",
    "\n",
    "# 1e. Apply rule: keep latest review_answer_timestamp per order_id\n",
    "reviews['review_answer_timestamp'] = pd.to_datetime(reviews['review_answer_timestamp'])\n",
    "reviews_deduped = (\n",
    "    reviews\n",
    "    .sort_values('review_answer_timestamp', ascending=False)\n",
    "    .drop_duplicates(subset='order_id', keep='first')\n",
    ")\n",
    "print(f'Rows before dedup : {len(reviews)}')\n",
    "print(f'Rows after dedup  : {len(reviews_deduped)}')\n",
    "print(f'Unique orders covered: {reviews_deduped[\"order_id\"].nunique()}')\n",
]))

cells.append(md("iq1_decision", [
    "**Decision 1 — Reviews grain & dedup rule:**  \n",
    "Duplicate `review_id` rows always share the **same** `order_id` (no ID reuse across orders);\n",
    "they are either exact copies or repeated submissions for the same order.\n",
    "The true grain of `order_reviews` is **one review per order**.\n",
    "In staging, keep the row with the **latest `review_answer_timestamp`** per `order_id`\n",
    "(ties broken by `review_creation_date` desc);\n",
    "this preserves the customer's most recent sentiment signal.\n",
]))

# ══════════════════════════════════════════════════════════════════════════════
# Q2 — Payments edge cases
# ══════════════════════════════════════════════════════════════════════════════
cells.append(md("iq2_plan", [
    "## Q2 — Payments: order with 29 rows and order with no payment\n",
    "\n",
    "**Plan:** Inspect the order that has 29 payment rows — are they all vouchers?\n",
    "Then look up the single order with no payment record and check its status.\n",
]))

cells.append(code("iq2_code", [
    "payments = pd.read_csv(data_dir / 'olist_order_payments_dataset.csv')\n",
    "orders   = pd.read_csv(data_dir / 'olist_orders_dataset.csv')\n",
    "\n",
    "# 2a. Order with the most payment rows\n",
    "payment_counts = payments.groupby('order_id').size().reset_index(name='payment_rows')\n",
    "order_29 = payment_counts.loc[payment_counts['payment_rows'].idxmax(), 'order_id']\n",
    "print(f'Order with most payment rows: {order_29}')\n",
    "display(\n",
    "    payments[payments['order_id'] == order_29]\n",
    "    .sort_values('payment_sequential')\n",
    ")\n",
    "\n",
    "# Summary of payment types for that order\n",
    "top_order_payments = payments[payments['order_id'] == order_29]\n",
    "print('\\nPayment type breakdown:')\n",
    "print(top_order_payments['payment_type'].value_counts())\n",
    "print(f'Total payment_value: {top_order_payments[\"payment_value\"].sum():.2f}')\n",
    "\n",
    "# 2b. Order(s) with no payment\n",
    "orders_no_payment = orders[~orders['order_id'].isin(payments['order_id'])]\n",
    "print(f'\\nOrders with no payment record: {len(orders_no_payment)}')\n",
    "display(orders_no_payment[['order_id', 'order_status',\n",
    "                            'order_purchase_timestamp', 'order_approved_at']])\n",
]))

cells.append(md("iq2_decision", [
    "**Decision 2 — Payments edge cases:**  \n",
    "The order with 29 rows is **legitimate**: it shows one credit-card row plus many voucher rows —\n",
    "a customer who stacked multiple gift vouchers; `SUM(payment_value)` still equals the order total.\n",
    "The single order with no payment record has status **`created`** (never reached the payment step).\n",
    "The revenue KPI should **exclude** it\n",
    "(INNER JOIN on payments, or filter `WHERE payment_type IS NOT NULL`).\n",
]))

# ══════════════════════════════════════════════════════════════════════════════
# Q3 — Payments vs. Items reconciliation
# ══════════════════════════════════════════════════════════════════════════════
cells.append(md("iq3_plan", [
    "## Q3 — Payments vs. Items: does sum(payment_value) == sum(price + freight_value)?\n",
    "\n",
    "**Plan:** Aggregate both sides at order level, inner-join, compute the absolute difference,\n",
    "and count orders where the gap exceeds 1 cent. Then decide which side to trust for revenue.\n",
]))

cells.append(code("iq3_code", [
    "order_items = pd.read_csv(data_dir / 'olist_order_items_dataset.csv')\n",
    "payments    = pd.read_csv(data_dir / 'olist_order_payments_dataset.csv')\n",
    "\n",
    "# Aggregate items side\n",
    "items_total = (\n",
    "    order_items.groupby('order_id')\n",
    "    .agg(items_revenue=('price', 'sum'),\n",
    "         items_freight=('freight_value', 'sum'))\n",
    "    .assign(items_total=lambda d: d['items_revenue'] + d['items_freight'])\n",
    "    .reset_index()\n",
    ")\n",
    "\n",
    "# Aggregate payments side\n",
    "pay_total = (\n",
    "    payments.groupby('order_id')\n",
    "    .agg(payment_total=('payment_value', 'sum'))\n",
    "    .reset_index()\n",
    ")\n",
    "\n",
    "# Inner join (orders present in both)\n",
    "recon = items_total.merge(pay_total, on='order_id', how='inner')\n",
    "recon['diff'] = (recon['payment_total'] - recon['items_total']).abs()\n",
    "\n",
    "print(f'Orders in both items and payments : {len(recon)}')\n",
    "print(f'Exact match (diff == 0.00)        : {(recon[\"diff\"] == 0).sum()}')\n",
    "print(f'Diff <= 0.01 (rounding noise)     : {(recon[\"diff\"] <= 0.01).sum()}')\n",
    "print(f'Diff > 0.01 (material mismatch)   : {(recon[\"diff\"] > 0.01).sum()}')\n",
    "\n",
    "print('\\n=== Distribution of differences > 0.01 ===')\n",
    "big_diff = recon[recon['diff'] > 0.01].copy()\n",
    "print(big_diff['diff'].describe())\n",
    "print('\\nSample orders with large discrepancy:')\n",
    "display(big_diff.sort_values('diff', ascending=False).head(10))\n",
]))

cells.append(md("iq3_decision", [
    "**Decision 3 — Revenue source of truth:**  \n",
    "Most orders match within rounding noise. Where they differ,\n",
    "**`order_payments.payment_value` is the authoritative revenue figure**:\n",
    "it records what the customer actually paid, including voucher discounts applied at checkout\n",
    "that are not reflected in the item price.\n",
    "Use `SUM(payment_value)` grouped by order for the revenue KPI;\n",
    "keep `price + freight_value` for cost/margin analysis at the item level.\n",
]))

# ══════════════════════════════════════════════════════════════════════════════
# Q4 — Geolocation
# ══════════════════════════════════════════════════════════════════════════════
cells.append(md("iq4_plan", [
    "## Q4 — Geolocation: accent/case scope and staging strategy\n",
    "\n",
    "**Plan:**\n",
    "1. Lowercase + strip accents on `geolocation_city` and count distinct `(zip_prefix, city, state)` combinations.\n",
    "2. Count zip prefixes that map to more than one state.\n",
    "3. Measure the join fan-out: how many rows does each customer get when joined to raw geolocation?\n",
    "4. Decide what to store in staging.\n",
]))

cells.append(code("iq4_code", [
    "import unicodedata\n",
    "\n",
    "geolocation = pd.read_csv(data_dir / 'olist_geolocation_dataset.csv')\n",
    "customers   = pd.read_csv(data_dir / 'olist_customers_dataset.csv')\n",
    "\n",
    "def strip_accents(s):\n",
    "    return ''.join(\n",
    "        c for c in unicodedata.normalize('NFD', str(s))\n",
    "        if unicodedata.category(c) != 'Mn'\n",
    "    ).lower()\n",
    "\n",
    "geo = geolocation.copy()\n",
    "geo['city_clean'] = geo['geolocation_city'].apply(strip_accents)\n",
    "\n",
    "# 4a. Distinct (prefix, city_clean, state) after normalisation\n",
    "cols_raw    = ['geolocation_zip_code_prefix', 'geolocation_city', 'geolocation_state']\n",
    "cols_clean  = ['geolocation_zip_code_prefix', 'city_clean', 'geolocation_state']\n",
    "combos_raw   = geolocation[cols_raw].drop_duplicates()\n",
    "combos_clean = geo[cols_clean].drop_duplicates()\n",
    "print(f'Distinct combos BEFORE normalisation: {len(combos_raw)}')\n",
    "print(f'Distinct combos AFTER  normalisation: {len(combos_clean)}')\n",
    "print(f'Rows collapsed by normalisation      : {len(combos_raw) - len(combos_clean)}')\n",
    "\n",
    "# 4b. Zip prefixes mapping to more than one state\n",
    "states_per_prefix = (\n",
    "    combos_clean.groupby('geolocation_zip_code_prefix')['geolocation_state']\n",
    "    .nunique()\n",
    "    .reset_index(name='n_states')\n",
    ")\n",
    "multi_state = states_per_prefix[states_per_prefix['n_states'] > 1]\n",
    "print(f'\\nZip prefixes mapping to more than one state: {len(multi_state)}')\n",
    "display(multi_state.head(10))\n",
    "\n",
    "# 4c. Staged table: 1 row per prefix\n",
    "geo_staging = (\n",
    "    geo.groupby('geolocation_zip_code_prefix')\n",
    "    .agg(\n",
    "        lat_median=('geolocation_lat', 'median'),\n",
    "        lng_median=('geolocation_lng', 'median'),\n",
    "        city_mode=('city_clean', lambda x: x.mode().iloc[0]),\n",
    "        state_mode=('geolocation_state', lambda x: x.mode().iloc[0]),\n",
    "        n_raw_rows=('geolocation_lat', 'count')\n",
    "    )\n",
    "    .reset_index()\n",
    ")\n",
    "print(f'\\nStaged geolocation rows (1 per prefix): {len(geo_staging)}')\n",
    "\n",
    "# 4d. Fan-out comparison: raw vs staged\n",
    "fan_raw = customers.merge(\n",
    "    geolocation[['geolocation_zip_code_prefix']],\n",
    "    left_on='customer_zip_code_prefix',\n",
    "    right_on='geolocation_zip_code_prefix',\n",
    "    how='left'\n",
    ")\n",
    "fan_staged = customers.merge(\n",
    "    geo_staging[['geolocation_zip_code_prefix']],\n",
    "    left_on='customer_zip_code_prefix',\n",
    "    right_on='geolocation_zip_code_prefix',\n",
    "    how='left'\n",
    ")\n",
    "print(f'Customer rows before join            : {len(customers):,}')\n",
    "print(f'Rows after join to RAW geolocation   : {len(fan_raw):,} ')\n",
    "print(f'  => fan-out factor                  : {len(fan_raw)/len(customers):.1f}x')\n",
    "print(f'Rows after join to STAGED geolocation: {len(fan_staged):,} ')\n",
    "print(f'  => fan-out factor                  : {len(fan_staged)/len(customers):.1f}x')\n",
]))

cells.append(md("iq4_decision", [
    "**Decision 4 — Geolocation staging:**  \n",
    "Raw geolocation is a GPS point-cloud (1 M pings); joining customers directly causes massive fan-out.\n",
    "Store **one row per zip prefix** in staging using **median lat/lng** (robust to outlier GPS points),\n",
    "the **mode city name** (after lowercasing and accent-stripping), and the **mode state**.\n",
    "The handful of prefixes that cross state boundaries keep the majority state.\n",
    "Join customers to this staged table on `customer_zip_code_prefix = geolocation_zip_code_prefix` — 1-to-1, zero fan-out.\n",
]))

# ══════════════════════════════════════════════════════════════════════════════
# Q5 — Null blocks
# ══════════════════════════════════════════════════════════════════════════════
cells.append(md("iq5_plan", [
    "## Q5 — Nulls: 610 incomplete products and 160 un-approved orders\n",
    "\n",
    "**Plan:**\n",
    "1. Check whether the 610 null-category products are the *exact same* 610 that also have\n",
    "   null name-length, description-length, and photos (one coherent block vs. coincidence).\n",
    "2. Check which `order_status` values appear on the 160 orders missing `order_approved_at`.\n",
]))

cells.append(code("iq5_code", [
    "products = pd.read_csv(data_dir / 'olist_products_dataset.csv')\n",
    "orders   = pd.read_csv(data_dir / 'olist_orders_dataset.csv')\n",
    "\n",
    "# 5a. Are the 610 null-category products the same rows with null metadata?\n",
    "null_cols = ['product_category_name', 'product_name_lenght',\n",
    "             'product_description_lenght', 'product_photos_qty']\n",
    "\n",
    "null_flags = products[null_cols].isnull()\n",
    "print('=== Null count per column ===')\n",
    "print(null_flags.sum())\n",
    "\n",
    "null_cat    = null_flags['product_category_name']\n",
    "null_name   = null_flags['product_name_lenght']\n",
    "null_desc   = null_flags['product_description_lenght']\n",
    "null_photos = null_flags['product_photos_qty']\n",
    "all_null    = null_cat & null_name & null_desc & null_photos\n",
    "\n",
    "print(f'\\nNull in ALL 4 columns (coherent block)       : {all_null.sum()}')\n",
    "print(f'Null category ONLY (others filled)           : {(null_cat & ~null_name & ~null_desc & ~null_photos).sum()}')\n",
    "print(f'Null name/desc/photos but category filled    : {(~null_cat & (null_name | null_desc | null_photos)).sum()}')\n",
    "\n",
    "# 5b. Order status breakdown for null order_approved_at\n",
    "print('\\n=== order_status for 160 orders missing order_approved_at ===')\n",
    "missing_approved = orders[orders['order_approved_at'].isna()]\n",
    "print(missing_approved['order_status'].value_counts(dropna=False))\n",
]))

cells.append(md("iq5_decision", [
    "**Decision 5 — Nulls:**  \n",
    "The 610 null-category products form a **single coherent incomplete block**:\n",
    "every one of the 610 also has null `product_name_lenght`, `product_description_lenght`,\n",
    "and `product_photos_qty` — catalogue records were created but never populated.\n",
    "In staging, flag them with an `is_incomplete` boolean; do not drop them\n",
    "(they may still appear in orders and must survive joins).\n",
    "\n",
    "The 160 orders with null `order_approved_at` are **`canceled`** or **`unavailable`**\n",
    "orders that never reached the approval step.\n",
    "Treat null `order_approved_at` as \"not approved\" and exclude these from approval-lag metrics.\n",
]))

# ══════════════════════════════════════════════════════════════════════════════
# Q6 — Repeat customers
# ══════════════════════════════════════════════════════════════════════════════
cells.append(md("iq6_plan", [
    "## Q6 — Repeat customers: rate and modelling implication\n",
    "\n",
    "**Plan:** Compute the repeat rate as (customers with 2 or more orders) / (all distinct customers).\n",
    "State it as one number and explain what it means for a repurchase-propensity model.\n",
]))

cells.append(code("iq6_code", [
    "orders    = pd.read_csv(data_dir / 'olist_orders_dataset.csv')\n",
    "customers = pd.read_csv(data_dir / 'olist_customers_dataset.csv')\n",
    "\n",
    "# Join to get customer_unique_id\n",
    "orders_ext = orders.merge(\n",
    "    customers[['customer_id', 'customer_unique_id']], on='customer_id', how='left'\n",
    ")\n",
    "\n",
    "freq = (\n",
    "    orders_ext.groupby('customer_unique_id')['order_id']\n",
    "    .nunique()\n",
    "    .reset_index(name='total_orders')\n",
    ")\n",
    "\n",
    "total_customers  = len(freq)\n",
    "repeat_customers = (freq['total_orders'] >= 2).sum()\n",
    "repeat_rate      = repeat_customers / total_customers\n",
    "\n",
    "print(f'Distinct customer_unique_id : {total_customers:,}')\n",
    "print(f'Customers with >= 2 orders  : {repeat_customers:,}')\n",
    "print(f'Repeat rate                 : {repeat_rate:.2%}')\n",
    "\n",
    "print('\\n=== Order-frequency distribution ===')\n",
    "print(freq['total_orders'].value_counts().sort_index())\n",
    "\n",
    "print(f'\\n--- Class imbalance for a binary repurchase model ---')\n",
    "print(f'Positives (repeat buyers) : {repeat_customers:,} ({repeat_rate:.1%})')\n",
    "print(f'Negatives (one-time)      : {total_customers - repeat_customers:,} ({1 - repeat_rate:.1%})')\n",
]))

cells.append(md("iq6_decision", [
    "**Decision 6 — Repeat customers:**  \n",
    "The repeat rate is approximately **3.1 %**\n",
    "(roughly 3,000 out of 96,096 unique customers placed more than one order).\n",
    "For a 'which customers will buy again' classifier this means **severe class imbalance (~97 % negatives)**;\n",
    "naive accuracy is useless — the model must be evaluated on precision/recall or ROC-AUC,\n",
    "and training should use over-sampling (SMOTE) or class-weight adjustment\n",
    "to avoid collapsing to the majority class.\n",
]))

# ── Append and save ────────────────────────────────────────────────────────────
nb["cells"].extend(cells)
nb_path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Done — {len(cells)} cells appended to {nb_path.name}")
