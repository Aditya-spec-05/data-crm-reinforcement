# DataScan CRM Cleaner v1.2

### Description
An AI-native environment for cleaning CRM databases. It simulates a data engineer's task of standardizing customer records across MariaDB/PostgreSQL/SQLite.

### Action Space
- `FIX_EMAIL`: Corrects malformed email strings.
- `FORMAT_PHONE`: Standardizes numbers to E.164.
- `CAPITALIZE_NAME`: Fixes casing and whitespace.

### Tasks
1. **Easy**: Fix 1 email record. (Score: 0.3)
2. **Medium**: Fix email and phone for 2 records. (Score: 0.6)
3. **Hard**: Full database standardization across 3+ records. (Score: 0.8+)

### Setup
1. `docker build -t crm-env .`
2. `docker run -p 7860:7860 crm-env`