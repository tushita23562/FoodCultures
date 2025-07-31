from flask import Flask, render_template, request, jsonify, redirect, session, url_for,flash
import psycopg2
import psycopg2.extras
import re
from markupsafe import Markup, escape

app = Flask(__name__)

conn = psycopg2.connect(
    dbname="FoodCulturesNew",
    user="postgres",
    password="23562",
    host="localhost",
    port="5432"
)

CATEGORY_HI_FALLBACK = {
    "Barley and millets": "जौ और बाजरा",
    "Greens and vegetables": "साग और सब्ज़ियाँ",
    "Other Collected Foods": "अन्य बटोरा हुआ खाद्य पदार्थ",
    "Groundnut and oilseeds": "मूँगफली और तिलहन पदार्थ",
    "Meat": "मांस",
    "Pulses": "दाल",
    "Sugarcane and jaggery": "गन्ना और गुड़",
    "Wheat and paddy": "गेहूँ और धान",
    "Hunger": "भूखमरी",
    "Dairy": "दुग्ध पदार्थ",
    "Fish": "मछलियाँ",
    "Fruit": "फल",
    "Land": "जमीन",
    "All": "सभी खान-पान"
}

def highlight_glossary(text, glossary):
    if re.search(r'<.*?>', text):
        return Markup(text)
    if not glossary:
        return Markup(escape(text))
    pattern = '|'.join(re.escape(g['term']) for g in glossary)
    regex = re.compile(r'\b(' + pattern + r')\b', re.IGNORECASE)
    def replacer(match):
        term = match.group(0)
        for g in glossary:
            if term.lower() == g['term'].lower():
                definition = escape(g['definition'])
                return f'<span class="glossary-term" data-definition="{definition}">{term}</span>'
        return escape(term)
    highlighted = regex.sub(replacer, escape(text))
    return Markup(highlighted)

app.jinja_env.filters['highlight_glossary'] = highlight_glossary

@app.route('/')
def redirect_home():
    return redirect('/category/12')


@app.route('/category/<int:food_category_id>')
def category(food_category_id):
    language = request.args.get('lang', 'en')

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT food_category_name FROM food_category_master WHERE food_category_id = %s", (food_category_id,))
    result = cur.fetchone()
    food_crop_name = result['food_category_name'] if result else "Unknown"

    cur.execute("SELECT food_category_name FROM food_category_other WHERE food_category_id = %s", (food_category_id,))
    hi_row = cur.fetchone()
    food_crop_name_hi = hi_row['food_category_name'] if hi_row else CATEGORY_HI_FALLBACK.get(food_crop_name)
    hindi_supported = bool(hi_row)

    if language == 'hi' and hindi_supported:
        timeline_crop_name = food_crop_name_hi
    else:
        timeline_crop_name = food_crop_name

    cur.execute("""
        SELECT tp.id, tp.label, t.transition, t.description
        FROM timeline t
        JOIN time_periods tp ON t.timeline_id = tp.id
        WHERE t.crop_name = %s
        ORDER BY tp.start_year, t.id
    """, (timeline_crop_name,))
    timeline = cur.fetchall()

    ### ✅ CASTE filters
    if food_category_id == 12:
        if language == 'hi':
            cur.execute("""
                SELECT DISTINCT c.caste_id, c.caste_name, o.caste_name AS caste_name_hi
                FROM crops_master cm
                JOIN caste_master c ON cm.caste_id = c.caste_id
                LEFT JOIN caste_other o ON c.caste_id = o.caste_id
            """)
        else:
            cur.execute("""
                SELECT DISTINCT c.caste_id, c.caste_name
                FROM crops_master cm
                JOIN caste_master c ON cm.caste_id = c.caste_id
            """)
    else:
        if language == 'hi' and hindi_supported:
            cur.execute("""
                SELECT DISTINCT c.caste_id, c.caste_name, o.caste_name AS caste_name_hi
                FROM crops_master cm
                JOIN caste_master c ON cm.caste_id = c.caste_id
                LEFT JOIN caste_other o ON c.caste_id = o.caste_id
                WHERE cm.food_category_id = %s
            """, (food_category_id,))
        else:
            cur.execute("""
                SELECT DISTINCT c.caste_id, c.caste_name
                FROM crops_master cm
                JOIN caste_master c ON cm.caste_id = c.caste_id
                WHERE cm.food_category_id = %s
            """, (food_category_id,))
    castes = [c for c in cur.fetchall() if (c.get('caste_name') or '').strip().lower()]

    ### ✅ SEASON filters
    if food_category_id == 12:
        if language == 'hi':
            cur.execute("""
                SELECT DISTINCT s.season_id, s.season_name, o.season_name AS season_name_hi
                FROM crops_master cm
                JOIN season_master s ON cm.season_id = s.season_id
                LEFT JOIN season_other o ON s.season_id = o.season_id
                
            """)
        else:
            cur.execute("""
                SELECT DISTINCT s.season_id, s.season_name
                FROM crops_master cm
                JOIN season_master s ON cm.season_id = s.season_id
                
            """)
    else:
        if language == 'hi' and hindi_supported:
            cur.execute("""
                SELECT DISTINCT s.season_id, s.season_name, o.season_name AS season_name_hi
                FROM crops_master cm
                JOIN season_master s ON cm.season_id = s.season_id
                LEFT JOIN season_other o ON s.season_id = o.season_id
                WHERE cm.food_category_id = %s 
            """, (food_category_id,))
        else:
            cur.execute("""
                SELECT DISTINCT s.season_id, s.season_name
                FROM crops_master cm
                JOIN season_master s ON cm.season_id = s.season_id
                WHERE cm.food_category_id = %s
            """, (food_category_id,))
    seasons = [s for s in cur.fetchall() if (s.get('season_name') or '').strip().lower()]

    ### ✅ GEOGRAPHY filters
    if food_category_id == 12:
        if language == 'hi':
            cur.execute("""
                SELECT DISTINCT g.geography_id, g.geography_name, o.geography_name AS geography_name_hi
                FROM crops_master cm
                JOIN geography_master g ON cm.geography_id = g.geography_id
                LEFT JOIN geography_other o ON g.geography_id = o.geography_id
            """)
        else:
            cur.execute("""
                SELECT DISTINCT g.geography_id, g.geography_name
                FROM crops_master cm
                JOIN geography_master g ON cm.geography_id = g.geography_id
            """)
    else:
        if language == 'hi' and hindi_supported:
            cur.execute("""
                SELECT DISTINCT g.geography_id, g.geography_name, o.geography_name AS geography_name_hi
                FROM crops_master cm
                JOIN geography_master g ON cm.geography_id = g.geography_id
                LEFT JOIN geography_other o ON g.geography_id = o.geography_id
                WHERE cm.food_category_id = %s
            """, (food_category_id,))
        else:
            cur.execute("""
                SELECT DISTINCT g.geography_id, g.geography_name
                FROM crops_master cm
                JOIN geography_master g ON cm.geography_id = g.geography_id
                WHERE cm.food_category_id = %s
            """, (food_category_id,))
    geographies = [g for g in cur.fetchall() if (g.get('geography_name') or '').strip().lower()]

    cur.execute("""
        SELECT m.food_category_id, m.food_category_name, o.food_category_name AS food_category_name_hi
        FROM food_category_master m
        LEFT JOIN food_category_other o ON m.food_category_id = o.food_category_id
        ORDER BY m.food_category_name
    """)
    food_categories = cur.fetchall()

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT term, definition FROM "Glossary"')
    Glossary = cur.fetchall()

    ### ✅ STATEMENTS: special-case ALL category
    if food_category_id == 12:
        cur.execute("""
            SELECT cm.statement,
                   c.caste_name, o_caste.caste_name AS caste_name_hi,
                   g.geography_name, o_geo.geography_name AS geography_name_hi,
                   s.season_name, o_season.season_name AS season_name_hi
            FROM crops_master cm
            LEFT JOIN caste_master c ON cm.caste_id = c.caste_id
            LEFT JOIN caste_other o_caste ON c.caste_id = o_caste.caste_id
            LEFT JOIN geography_master g ON cm.geography_id = g.geography_id
            LEFT JOIN geography_other o_geo ON g.geography_id = o_geo.geography_id
            LEFT JOIN season_master s ON cm.season_id=s.season_id
            LEFT JOIN season_other o_season ON s.season_id=o_season.season_id
            WHERE cm.statement_language = %s
        """, ('hi' if language == 'hi' else 'en',))
    else:
        cur.execute("""
            SELECT cm.statement,
                   c.caste_name, o_caste.caste_name AS caste_name_hi,
                   g.geography_name, o_geo.geography_name AS geography_name_hi,
                   s.season_name, o_season.season_name AS season_name_hi 
            FROM crops_master cm
            LEFT JOIN caste_master c ON cm.caste_id = c.caste_id
            LEFT JOIN caste_other o_caste ON c.caste_id = o_caste.caste_id
            LEFT JOIN geography_master g ON cm.geography_id = g.geography_id
            LEFT JOIN geography_other o_geo ON g.geography_id = o_geo.geography_id
            LEFT JOIN season_master s ON cm.season_id=s.season_id
            LEFT JOIN season_other o_season ON s.season_id=o_season.season_id        
            WHERE cm.food_category_id = %s AND cm.statement_language = %s
        """, (food_category_id, 'hi' if language == 'hi' else 'en'))

    initial_statements = cur.fetchall()
    seen = set()
    unique_statements = []
    for row in initial_statements:
        key = (
            row['statement'].strip() if row['statement'] else '',
            row.get('caste_name') or row.get('caste_name_hi') or '',
            row.get('geography_name') or row.get('geography_name_hi') or '',
            row.get('season_name') or row.get('season_name_hi') or ''
        )
        if key not in seen:
            seen.add(key)
            unique_statements.append(row)

    media_types = set()
    for row in initial_statements:
        s = row['statement'].lower()
        if 'youtube' in s:
            media_types.add('Video')
        elif 'imagekit' in s or s.endswith(('.jpg', '.png')):
            media_types.add('Image')
        else:
            media_types.add('Text')

    media_types = sorted(media_types)

    return render_template(
        'category.html',
        timeline=timeline,
        castes=castes,
        seasons=seasons,
        geographies=geographies,
        media_types=media_types,
        food_category_id=food_category_id,
        food_crop_name=food_crop_name,
        food_crop_name_hi=food_crop_name_hi,
        food_categories=food_categories,
        hindi_supported=hindi_supported,
        language=language,
        fallback=CATEGORY_HI_FALLBACK,
        Glossary=Glossary,
        initial_statements=unique_statements
    )

@app.route('/get_statements', methods=['POST'])
def get_statements():
    data = request.json
    food_category_id = data['food_category_id']
    caste_ids = data.get('caste_ids') or None
    season_ids = data.get('season_ids') or None
    geography_ids = data.get('geography_ids') or None
    language = data.get('language', 'en')
    media_types_filter = data.get('media_types') or []
    statement_language = 'hi' if language == 'hi' else 'en'

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        if food_category_id == 12:
            cur.execute("""
                SELECT cm.statement,
                       c.caste_name, o_caste.caste_name AS caste_name_hi,
                       g.geography_name, o_geo.geography_name AS geography_name_hi,
                       s.season_name, o_season.season_name AS season_name_hi
                FROM crops_master cm
                LEFT JOIN caste_master c ON cm.caste_id = c.caste_id
                LEFT JOIN caste_other o_caste ON c.caste_id = o_caste.caste_id
                LEFT JOIN geography_master g ON cm.geography_id = g.geography_id
                LEFT JOIN geography_other o_geo ON g.geography_id = o_geo.geography_id
                LEFT JOIN season_master s ON cm.season_id=s.season_id
                LEFT JOIN season_other o_season ON s.season_id=o_season.season_id
                WHERE (%s::int[] IS NULL OR cm.caste_id = ANY(%s::int[]))
                  AND (%s::int[] IS NULL OR cm.season_id = ANY(%s::int[]))
                  AND (%s::int[] IS NULL OR cm.geography_id = ANY(%s::int[]))
                  AND cm.statement_language = %s
            """, (
                caste_ids, caste_ids,
                season_ids, season_ids,
                geography_ids, geography_ids,
                statement_language
            ))
        else:
            cur.execute("""
                SELECT cm.statement,
                       c.caste_name, o_caste.caste_name AS caste_name_hi,
                       g.geography_name, o_geo.geography_name AS geography_name_hi,
                       s.season_name, o_season.season_name AS season_name_hi 
                FROM crops_master cm
                LEFT JOIN caste_master c ON cm.caste_id = c.caste_id
                LEFT JOIN caste_other o_caste ON c.caste_id = o_caste.caste_id
                LEFT JOIN geography_master g ON cm.geography_id = g.geography_id
                LEFT JOIN geography_other o_geo ON g.geography_id = o_geo.geography_id
                LEFT JOIN season_master s ON cm.season_id=s.season_id 
                LEFT JOIN season_other o_season ON s.season_id=o_season.season_id
                WHERE cm.food_category_id = %s
                  AND (%s::int[] IS NULL OR cm.caste_id = ANY(%s::int[]))
                  AND (%s::int[] IS NULL OR cm.season_id = ANY(%s::int[]))
                  AND (%s::int[] IS NULL OR cm.geography_id = ANY(%s::int[]))
                  AND cm.statement_language = %s
            """, (
                food_category_id,
                caste_ids, caste_ids,
                season_ids, season_ids,
                geography_ids, geography_ids,
                statement_language
            ))

        statements = cur.fetchall()
        seen = set()
        unique_statements = []
        for row in statements:
            text = (row['statement'] or '').lower()
            media_type = 'Video' if 'youtube' in text else 'Image' if 'imagekit' in text or text.endswith(('.jpg', '.png')) else 'Text'
            if media_types_filter and media_type not in media_types_filter:
                continue
            key = (
                row['statement'].strip() if row['statement'] else '',
                row.get('caste_name') or row.get('caste_name_hi') or '',
                row.get('geography_name') or row.get('geography_name_hi') or '',
                row.get('season_name') or row.get('season_name_hi') or ''
            )
            if key not in seen:
                seen.add(key)
                unique_statements.append(row)

        cur.execute('SELECT term, definition FROM "Glossary"')
        Glossary = cur.fetchall()

        conn.commit()
        return jsonify({'statements': unique_statements, 'Glossary': Glossary})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    
CATEGORY_ID_MAP = {
    "Sugarcane and jaggery": 1,
    "Fish": 2,
    "Dairy": 3,
    "Pulses": 4,
    "Meat": 5,
    "Other Collected Foods": 6,  
    "Land": 7,
    "Groundnut and oilseeds": 8,  
    "Fruit": 9,
    "Barley and millets": 10,
    "Wheat and paddy": 11,
    "Greens and vegetables": 13,
    "Hunger": 14,
    "All": 12
}

@app.route("/about")
def about():
    return render_template("aboutus.html")

@app.route("/contactus")
def contactus():
    return render_template("contactus.html")

@app.route("/send-email", methods=["POST"])
def send_email():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")
    number = data.get("number")

    # Implement your email sending logic here
    try:
        # Example only: replace with working logic
        print(f"Sending email from {name} ({email}), number: {number}\nMessage: {message}")
        return jsonify({"success": True, "message": "Email sent!"})
    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": str(e)})
    
@app.route('/resources')
def resources():
    return render_template('resources.html')

def validate_excel(df):
    required_columns = [
        'statement', 'statement_language', 'reference',
        'food_category', 'caste', 'geography', 'season', 'category',
        'datatype', 'time_period'
    ]
    for col in required_columns:
        if col not in df.columns:
            return False

    # Validate time_period (e.g., 1980 or 1980-1989)
    time_period_pattern = r"^\d{4}(-\d{4})?$"
    if not df['time_period'].apply(lambda x: bool(re.match(time_period_pattern, str(x)))).all():
        return False

    # Capitalization check (skip 'statement')
    for col in ['food_category', 'caste', 'geography', 'season', 'category', 'datatype']:
        if not df[col].apply(lambda x: str(x).istitle()).all():
            return False

    # Check that statement column URLs are hyperlinks
    if df['statement'].str.contains("http").any():
        if not df['statement'].apply(lambda x: x.startswith("http")).all():
            return False

    return True

def insert_data_to_db(df):
    conn = psycopg2.connect(dbname="FoodCulturesNew", user="postgres", password="yourpass", host="localhost")
    cur = conn.cursor()

    for _, row in df.iterrows():
        # You must map string values to their respective IDs from *_master tables
        cur.execute("SELECT caste_id FROM caste_master WHERE caste_name = %s", (row['caste'],))
        caste_id = cur.fetchone()
        if not caste_id:
            raise Exception(f"Caste '{row['caste']}' not found.")
        
        # Do the same for all other FK fields (category, datatype, food_category, etc.)

        # Insert into crops_master (example)
        cur.execute("""
            INSERT INTO crops_master (
                statement, statement_language, reference,
                food_category_id, caste_id, geography_id,
                season_id, category_id, datatype_id,
                time_period_id,
                season_language, caste_language, category_language, datatype_language, geography_language, food_category_language
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s)
        """, (
            row['statement'], row['statement_language'], row['reference'],
            get_id('food_category_master', row['food_category'], cur),
            get_id('caste_master', row['caste'], cur),
            get_id('geography_master', row['geography'], cur),
            get_id('season_master', row['season'], cur),
            get_id('category_master', row['category'], cur),
            get_id('datatype_master', row['datatype'], cur),
            get_time_period_id(row['time_period'], cur),
            ['en'] if row['statement_language'] == 'en' else ['hi'],  # all language fields
            ['en'], ['en'], ['en'], ['en'], ['en']
        ))

    conn.commit()
    cur.close()
    conn.close()

app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'your-secret-key'

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "23562"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/upload')
        else:
            flash("Invalid credentials")
            return redirect('/login')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash("Logged out.")
    return redirect('/')

@app.route('/upload', methods=['GET', 'POST'])
def upload_excel():
    if not session.get('admin'):
        return redirect('/login')

    if request.method == 'POST':
        file = request.files['excel_file']
        if not file.filename.endswith('.xlsx'):
            flash("Only .xlsx files allowed.")
            return redirect('/upload')

        path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(path)

        try:
            df = pd.read_excel(path)

            if not validate_excel(df):
                flash("Excel format is invalid. Please follow the template strictly.")
                return redirect('/upload')

            insert_data_to_db(df)
            flash("File uploaded and data inserted successfully.")
        except Exception as e:
            flash(f"Error: {str(e)}")

    return render_template("upload.html")

@app.before_request
def auto_logout():
    if request.endpoint not in ('upload_excel', 'login', 'static'):
        session.pop('admin', None)

def validate_excel(df):
    required_columns = [
        'statement', 'statement_language', 'reference',
        'food_category', 'caste', 'geography', 'season', 'category',
        'datatype', 'time_period'
    ]
    for col in required_columns:
        if col not in df.columns:
            return False

    time_period_pattern = r"^\d{4}(-\d{4})?$"
    if not df['time_period'].apply(lambda x: bool(re.match(time_period_pattern, str(x)))).all():
        return False

    for col in ['food_category', 'caste', 'geography', 'season', 'category', 'datatype']:
        if not df[col].apply(lambda x: str(x).istitle()).all():
            return False

    if df['statement'].str.contains("http").any():
        if not df['statement'].apply(lambda x: x.startswith("http")).all():
            return False

    return True

def insert_data_to_db(df):
    cur = conn.cursor()
    for _, row in df.iterrows():
        cur.execute("SELECT caste_id FROM caste_master WHERE caste_name = %s", (row['caste'],))
        caste_id = cur.fetchone()
        if not caste_id:
            raise Exception(f"Caste '{row['caste']}' not found.")

        cur.execute("""
            INSERT INTO crops_master (
                statement, statement_language, reference,
                food_category_id, caste_id, geography_id,
                season_id, category_id, datatype_id,
                time_period_id,
                season_language, caste_language, category_language, datatype_language, geography_language, food_category_language
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s)
        """, (
            row['statement'], row['statement_language'], row['reference'],
            get_id('food_category_master', row['food_category'], cur),
            get_id('caste_master', row['caste'], cur),
            get_id('geography_master', row['geography'], cur),
            get_id('season_master', row['season'], cur),
            get_id('category_master', row['category'], cur),
            get_id('datatype_master', row['datatype'], cur),
            get_time_period_id(row['time_period'], cur),
            ['en'] if row['statement_language'] == 'en' else ['hi'],
            ['en'], ['en'], ['en'], ['en'], ['en']
        ))
    conn.commit()
    cur.close()

def get_id(table, value, cur):
    cur.execute(f"SELECT {table.split('_')[0]}_id FROM {table} WHERE {table.split('_')[0]}_name = %s", (value,))
    result = cur.fetchone()
    if not result:
        raise Exception(f"'{value}' not found in {table}")
    return result[0]

def get_time_period_id(label, cur):
    if '-' in label:
        start_year, end_year = map(int, label.split('-'))
    else:
        start_year = end_year = int(label)
    cur.execute("""
        SELECT id FROM time_periods
        WHERE start_year = %s AND end_year = %s
    """, (start_year, end_year))
    result = cur.fetchone()
    if not result:
        raise Exception(f"Time period '{label}' not found.")
    return result[0]

@app.context_processor
def inject_session():
    return dict(session=session)

if __name__ == '__main__':
     app.run(debug=True)

