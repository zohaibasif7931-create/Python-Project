import os
import sqlite3
import pandas as pd
import csv
import joblib
from flask import Flask, request, redirect, url_for
from flask import Flask, render_template, g, request, redirect, url_for
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

app = Flask(__name__, template_folder='.')

# === Settings ===
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "phones.db")
MODEL_PATH = os.path.join(BASE_DIR, "buy_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")
RECOMMENDATIONS_CSV = os.path.join(BASE_DIR, "recommendations.csv")
FEEDBACK_CSV = os.path.join(BASE_DIR, "feedback.csv")

USE_SCALER = False

BRANDS = ['oppo', 'vivo', 'infinix', 'tecno', 'iphone', 'samsung', 'xiaomi']

FEATURE_COLS = [
    'camera', 'battery', 'screen', 'processor',
    'ram', 'storage', 'build_quality', 'price_pta'
]

FEEDBACK_FILE = 'feedback.csv'
STAR_TRACKER_FILE = 'model_stars.csv'  # For tracking model star ratings
SATISFACTION_CSV = os.path.join(BASE_DIR, "satisfaction.csv")


# === Database connection ===
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db:
        db.close()


# === Model training ===
def build_training_data():
    conn = sqlite3.connect(DB_PATH)
    df_list = []
    for brand in BRANDS:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {brand}", conn)
            df['brand'] = brand
            df_list.append(df)
        except Exception as e:
            print(f"Skipping brand {brand} due to error: {e}")
    conn.close()
    full_df = pd.concat(df_list, ignore_index=True)

    for col in FEATURE_COLS:
        if col not in full_df.columns:
            full_df[col] = 0
        full_df[col] = pd.to_numeric(full_df[col], errors='coerce').fillna(0)

    return full_df


def train_model():
    df = build_training_data()
    X = df[FEATURE_COLS].values

    if USE_SCALER:
        scaler = StandardScaler()
        X = scaler.fit_transform(X)
        joblib.dump(scaler, SCALER_PATH)

    model = NearestNeighbors(n_neighbors=5)
    model.fit(X)
    joblib.dump((model, df), MODEL_PATH)


# === Routes ===
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/buy_choose')
def buy_choose():
    return render_template('buy_choose.html')


@app.route('/buy/manual', methods=['GET', 'POST'])
def buy_manual():
    db = get_db()
    cursor = db.cursor()
    brands = BRANDS.copy()
    selected_brand = request.form.get('brand')
    selected_category = request.form.get('category')
    selected_model = request.form.get('model')

    categories, models = [], []
    price_pta = price_non_pta = None

    if selected_brand:
        cursor.execute(f"SELECT DISTINCT category FROM {selected_brand}")
        categories = [r['category'] for r in cursor.fetchall()]
    if selected_brand and selected_category:
        cursor.execute(f"SELECT model FROM {selected_brand} WHERE category = ?", (selected_category,))
        models = [r['model'] for r in cursor.fetchall()]
    if selected_brand and selected_model:
        cursor.execute(f"SELECT price_pta, price_non_pta FROM {selected_brand} WHERE model = ?", (selected_model,))
        row = cursor.fetchone()
        if row:
            price_pta, price_non_pta = row['price_pta'], row['price_non_pta']

    return render_template('buy_manual.html', brands=brands, categories=categories, models=models,
                           selected_brand=selected_brand, selected_category=selected_category,
                           selected_model=selected_model, price_pta=price_pta, price_non_pta=price_non_pta)


@app.route('/sell', methods=['GET', 'POST'])
def sell():
    db = get_db()
    cursor = db.cursor()
    brands = BRANDS.copy()
    selected_brand = request.form.get('brand')
    selected_category = request.form.get('category')
    selected_model = request.form.get('model')
    battery_rating = request.form.get('battery_rating', '3')
    camera_rating = request.form.get('camera_rating', '3')
    back_glass_rating = request.form.get('back_glass_rating', '3')
    display_rating = request.form.get('display_rating', '3')

    categories, models = [], []
    price_pta = price_non_pta = None
    discount_applied = 0

    if selected_brand:
        cursor.execute(f"SELECT DISTINCT category FROM {selected_brand}")
        categories = [r['category'] for r in cursor.fetchall()]
    if selected_brand and selected_category:
        cursor.execute(f"SELECT model FROM {selected_brand} WHERE category = ?", (selected_category,))
        models = [r['model'] for r in cursor.fetchall()]
    if request.method == 'POST' and selected_model:
        cursor.execute(f"SELECT price_pta, price_non_pta FROM {selected_brand} WHERE model = ?", (selected_model,))
        row = cursor.fetchone()
        if row:
            price_pta, price_non_pta = row['price_pta'], row['price_non_pta']
            ratings = [
                int(battery_rating),
                int(camera_rating),
                int(back_glass_rating),
                int(display_rating)
            ]
            # Discount mapping: 1=Poor(-10%), 2=Fair(-5%), 3=Good(0%)
            def rating_to_discount(r): 
                if r == 1:  # Poor
                    return 10
                elif r == 2:  # Fair
                    return 5
                else:  # Good (3)
                    return 0
            
            # Calculate total discount (sum of all individual discounts)
            discount_applied = sum(map(rating_to_discount, ratings))
            # Cap maximum discount at 40% (10*4 fields max)
            discount_applied = min(discount_applied, 40)
            
            price_pta = int(price_pta * (1 - discount_applied / 100))
            price_non_pta = int(price_non_pta * (1 - discount_applied / 100))

    return render_template('sell.html', brands=brands, categories=categories, models=models,
                           selected_brand=selected_brand, selected_category=selected_category,
                           selected_model=selected_model, price_pta=price_pta, price_non_pta=price_non_pta,
                           discount_applied=discount_applied, battery_rating=battery_rating,
                           camera_rating=camera_rating, back_glass_rating=back_glass_rating,
                           display_rating=display_rating)


@app.route('/buy_recommendations', methods=['GET', 'POST'])
def buy_recommendations():
    if request.method == 'POST':
        try:
            # Check if all required fields are present
            missing_fields = [col for col in FEATURE_COLS if col not in request.form]
            if missing_fields:
                return render_template('buy_recommendations.html', error=f"Missing fields: {', '.join(missing_fields)}")
            
            user_input = {col: int(request.form[col]) for col in FEATURE_COLS}
            user_df = pd.DataFrame([user_input])

            model, df = joblib.load(MODEL_PATH)
            X = df[FEATURE_COLS].values
            user_vals = user_df[FEATURE_COLS].values

            if USE_SCALER and os.path.exists(SCALER_PATH):
                scaler = joblib.load(SCALER_PATH)
                X = scaler.transform(X)
                user_vals = scaler.transform(user_vals)

            distances, indices = model.kneighbors(user_vals, n_neighbors=10)
            all_recommendations = df.iloc[indices[0]][['brand', 'model', 'price_pta']].to_dict('records')

            # Filter out models with -3 or lower stars from satisfaction.csv
            try:
                if os.path.exists(SATISFACTION_CSV):
                    satisfaction_df = pd.read_csv(SATISFACTION_CSV)
                    # Get models with stars <= -3
                    blocked_entries = satisfaction_df[satisfaction_df['stars'] <= -3]
                    
                    # Filter recommendations to get valid ones
                    filtered_recommendations = []
                    blocked_count = 0
                    for rec in all_recommendations:
                        is_blocked = False
                        brand = rec['brand']
                        model_name = rec['model']
                        price = rec['price_pta']
                        
                        # Check against all blocked entries using multiple matching strategies
                        for _, blocked_row in blocked_entries.iterrows():
                            blocked_model = blocked_row['model']
                            blocked_price = blocked_row['price_pta']
                            blocked_brand = blocked_row['brand'] if pd.notna(blocked_row['brand']) else ''
                            
                            # Match by model name, price, and brand (case-insensitive)
                            if (model_name.lower() == blocked_model.lower() and 
                                price == blocked_price):
                                is_blocked = True
                                blocked_count += 1
                                print(f"⛔ BLOCKED: {model_name} ({brand}) at ₨{price} - Stars: {blocked_row['stars']}")
                                break
                        
                        if not is_blocked:
                            filtered_recommendations.append(rec)
                        
                        # Stop if we have at least 3 valid recommendations
                        if len(filtered_recommendations) >= 3:
                            break
                    
                    recommendations = filtered_recommendations
                    print(f"📊 Blocked: {blocked_count}, Valid recommendations: {len(recommendations)}")
                else:
                    recommendations = all_recommendations[:3]
            except Exception as e:
                print(f"❌ Error filtering satisfaction data: {e}")
                recommendations = all_recommendations[:3]

            os.makedirs('db', exist_ok=True)
            with open(os.path.join('db', 'feedback.csv'), 'a', newline='') as f:
                csv.writer(f).writerow([user_input[c] for c in FEATURE_COLS])

            return render_template('buy_result.html', models=recommendations)

        except Exception as e:
            return render_template('buy_recommendations.html', error=f"Error: {str(e)}")

    return render_template('buy_recommendations.html')

# Expected columns
CSV_COLUMNS = ['model', 'price_pta', 'camera', 'battery', 'screen', 'processor', 'ram', 'storage', 'build_quality']

# Ensure CSV files exist
def ensure_csv_file(path, columns):
    if not os.path.exists(path) or os.stat(path).st_size == 0:
        with open(path, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(columns)

# Load dataframe safely
def load_csv_dataframe(path, columns):
    try:
        return pd.read_csv(path)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=columns)

ensure_csv_file(RECOMMENDATIONS_CSV, CSV_COLUMNS + ['stars'])
ensure_csv_file(FEEDBACK_CSV, CSV_COLUMNS)

@app.route('/feedback', methods=['POST'])
def feedback():
    action = request.form.get("action")
    combo_key = request.form.get("combo_key")
    model = request.form.get("model", "")
    brand = request.form.get("brand", "")
    price_pta = request.form.get("price_pta", "")

    if not combo_key or action not in ['satisfied', 'dissatisfied']:
        return render_template("thankyou.html")

    try:
        satisfaction_df = pd.read_csv(SATISFACTION_CSV)
    except FileNotFoundError:
        satisfaction_df = pd.DataFrame(columns=["combo_key", "model", "brand", "price_pta", "stars"])

    if combo_key in satisfaction_df["combo_key"].values:
        index = satisfaction_df[satisfaction_df["combo_key"] == combo_key].index[0]
        satisfaction_df.at[index, "stars"] += 1 if action == "satisfied" else -1
    else:
        stars = 1 if action == "satisfied" else -1
        satisfaction_df = pd.concat([
            satisfaction_df,
            pd.DataFrame([{"combo_key": combo_key, "model": model, "brand": brand, "price_pta": price_pta, "stars": stars}])
        ], ignore_index=True)

    satisfaction_df.to_csv(SATISFACTION_CSV, index=False)

    return render_template("thankyou.html")



if __name__ == '__main__':
    train_model()
    app.run(debug=True)
