from flask import Flask, session, request, redirect, url_for, render_template, flash
from flask_session import Session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import calendar
from datetime import datetime
from gpt import ask_chatgpt
import pandas as pd
from chart import create_chart


app = Flask(__name__)
app.config['SECRET_KEY'] = 'joon'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

db_config = {
    'user': 'joon',
    'password': '1234',
    'host': 'localhost',
    'database': 'backend'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def fetch_data(query, params=None):
    connection = get_db_connection()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        records = cursor.fetchall()
        cursor.close()
    finally:
        connection.close()
    
    return records

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        user_id = request.form['user_id']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        phone = request.form['phone']
        birth = request.form['birth']
        gender = request.form['gender']
        height = request.form['height']
        weight = request.form['weight']
        
        if password == confirm_password:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            existing_user = cursor.fetchone()
            flash('회원가입 성공')
            
            if existing_user:
                flash('아이디 중복')
                cursor.close()
                db.close()
                return redirect(url_for('signup'))
            
            cursor.execute("INSERT INTO users (username, user_id, password, email, phone, birth, gender, height, weight) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (username, user_id, hashed_password, email, phone, birth, gender, height, weight))
            db.commit()
            cursor.close()
            db.close()
            return redirect(url_for('login'))
        else:
            flash('비밀번호 불일치')
            return redirect(url_for('signup'))
            
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user['password'], password):
            session['id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('main'))
        else:
            flash('로그인 실패')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/main')
def main():
    if 'id' not in session:
        return redirect(url_for('login'))
    
    year = request.args.get('year', type=int, default=datetime.now().year)
    month = request.args.get('month', type=int, default=datetime.now().month)
    
    cal = calendar.monthcalendar(year, month)
    
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    now = datetime.now()
    
    return render_template('main.html', 
                           now=now,
                           year=year, 
                           month=month, 
                           calendar=cal,
                           prev_year=prev_year,
                           prev_month=prev_month,
                           next_year=next_year,
                           next_month=next_month)

@app.route('/memo/<int:year>/<int:month>/<int:day>')
def memo(year, month, day):
    if 'id' not in session:
        return redirect(url_for('login'))
    
    date = f"{year}-{month:02d}-{day:02d}"
    user_id = session['id']
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT et.id, et.description, ue.exercise_number
        FROM exercise_types et
        JOIN user_exercises ue ON et.id = ue.exercise_type_id
        WHERE ue.user_id = %s AND ue.date = %s
    """, (user_id, date))
    exercises = cursor.fetchall()
    
    exercises_detail = {}
    for exercise in exercises:
        cursor.execute("""
            SELECT exercise_name, exercise_set, exercise_weight , exercise_count
            FROM exercise_items 
            WHERE user_exercise_id IN (
                SELECT id FROM user_exercises 
                WHERE user_id = %s AND date = %s AND exercise_number = %s
            )
        """, (user_id, date, exercise['exercise_number']))
        exercises_detail[exercise['exercise_number']] = cursor.fetchall()
    
    cursor.execute("SELECT recommendation FROM exercise_recommendations WHERE user_id = %s AND date = %s ORDER BY id DESC LIMIT 1", (user_id, date))
    recommendation = cursor.fetchone()
    chatgpt_recommendation = recommendation['recommendation'] if recommendation else None
    
    cursor.close()
    db.close()
    
    return render_template('memo.html', year=year, month=month, day=day, exercises=exercises, exercises_detail=exercises_detail, chatgpt_recommendation=chatgpt_recommendation)

@app.route('/update_exercise', methods=['POST'])
def update_exercise():
    if 'id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['id']
    date = request.form['date']
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("DELETE FROM user_exercises WHERE user_id = %s AND date = %s", (user_id, date))
        
        exercise_types_name = [request.form.get(f'exercise_type{i}', '') for i in range(1, 4) if request.form.get(f'exercise_type{i}')]
        
        exercise_types_ids = []
        for name in exercise_types_name:
            if name:
                sql = "SELECT id FROM exercise_types WHERE name = %s"
                cursor.execute(sql, (name,))
                result = cursor.fetchone()
                if result:
                    exercise_types_ids.append(result['id'])
        
        for exercise_number, exercise_type_id in enumerate(exercise_types_ids, start=1):
            cursor.execute("INSERT INTO user_exercises (user_id, date, exercise_number, exercise_type_id) VALUES (%s, %s, %s, %s)", 
                           (user_id, date, exercise_number, exercise_type_id))
            user_exercise_id = cursor.lastrowid
            
            for set_number in range(1, 6):
                exercise_name = request.form.get(f'exercise_name{exercise_number}_{set_number}')
                exercise_set = request.form.get(f'exercise_set{exercise_number}_{set_number}')
                exercise_weight = request.form.get(f'exercise_weight{exercise_number}_{set_number}')
                exercise_count = request.form.get(f'exercise_count{exercise_number}_{set_number}')
                
                if exercise_name:
                    cursor.execute("INSERT INTO exercise_items (user_exercise_id, exercise_name, exercise_set, exercise_weight, exercise_count) VALUES (%s, %s, %s, %s, %s)",
                                   (user_exercise_id, exercise_name, exercise_set, exercise_weight, exercise_count))
        
        db.commit()
        flash('저장 되었습니다.')
        
    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
        flash('오류가 발생했습니다.')
    
    finally:
        cursor.close()
        db.close()
    
    year, month, day = map(int, date.split('-'))
    return redirect(url_for('memo', year=year, month=month, day=day))


@app.route('/delete_exercise', methods=['POST'])
def delete_exercise():
    if 'id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['id']
    date = request.form['date']
    
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            DELETE ei FROM exercise_items ei
            JOIN user_exercises ue ON ei.user_exercise_id = ue.id
            WHERE ue.user_id = %s AND ue.date = %s
        """, (user_id, date))
        
        cursor.execute("DELETE FROM user_exercises WHERE user_id = %s AND date = %s", (user_id, date))
        
        db.commit()
        flash('삭제 되었습니다.')
    except Exception as e:
        db.rollback()
        flash('삭제 중 오류가 발생했습니다.')
        print(f"An error occurred: {e}")
    finally:
        cursor.close()
        db.close()
    
    year, month, day = map(int, date.split('-'))
    return redirect(url_for('memo', year=year, month=month, day=day))

@app.route('/gpt_show', methods=['GET', 'POST'])
def gpt_show():
    if 'id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['id']
    date = request.form['date']
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT birth, gender, height, weight FROM user WHERE id = %s", (user_id,))
    user_info = cursor.fetchone()
    
    cursor.execute("SELECT exercise_type_id FROM user_exercises WHERE user_id = %s AND date = %s", (user_id, date))
    exercise_type_ids = cursor.fetchall()
    
    if not exercise_type_ids:
        flash('선택된 운동이 없습니다.')
        year, month, day = map(int, date.split('-'))
        return redirect(url_for('memo', year=year, month=month, day=day))
    
    exercise_type_ids_list = [et['exercise_type_id'] for et in exercise_type_ids]
    
    cursor.execute("SELECT id, description FROM exercise_types WHERE id IN (%s)" % ','.join(['%s']*len(exercise_type_ids_list)), exercise_type_ids_list)
    exercise_info = cursor.fetchall()
    
    exercise_info_text = ', '.join([info['description'] for info in exercise_info])
    prompt = f"""사용자 정보: 생년월일 {user_info['birth']}, 성별 {user_info['gender']}, 키 {user_info['height']}cm, 체중 {user_info['weight']}kg

                선택한 운동: {exercise_info_text}

                위 선택한 운동에 맞는 운동 종목 3가지씩 세트수랑 무게랑 횟수를 사용자 정보에 맞게 추천해주세요. 각 운동 종목에 대한 설명도 간략하게 추가해주세요. 
                다음 형식으로 응답해주세요:

                1. [운동 종류 1]
                a. [운동 종목 1]: [세트 수]set ([횟수]times x [무게]kg)
                    설명: [간단한 설명]

                b. [운동 종목 2]: [세트 수]set ([횟수]times x [무게]kg)
                    설명: [간단한 설명]

                c. [운동 종목 3]: [세트 수]set ([횟수]times x [무게]kg)
                    설명: [간단한 설명]

                2. [운동 종류 2]
                ...

                각 운동 종류와 종목 사이, 그리고 각 운동 종목의 설명 뒤에는 빈 줄을 넣어 구분해주세요."""

    recommendation = ask_chatgpt(prompt)
    recommendation = recommendation.replace('\n', '<br>')

    try:
        cursor.execute("INSERT INTO exercise_recommendations (user_id, date, recommendation) VALUES (%s, %s, %s)", (user_id, date, recommendation))
        db.commit()
    finally:
        cursor.close()
        db.close()

    flash('추천 완성되었습니다.')
    year, month, day = map(int, date.split('-'))
    return redirect(url_for('memo', year=year, month=month, day=day))

@app.route('/chart', methods=['GET', 'POST'])
def chart():
    if 'id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['id']
    
    query = """
    SELECT et.description, COUNT(ue.exercise_type_id) AS count
    FROM exercise_types et
    JOIN user_exercises ue ON et.id = ue.exercise_type_id
    WHERE ue.user_id = %s
    GROUP BY et.description
    """
    data = fetch_data(query, (user_id,))
    df = pd.DataFrame(data, columns=['description', 'count'])
    
    print(f"DataFrame content: {df}")   
    
    chart_filename = ''
    if not df.empty:
        chart_filename = create_chart(df, '운동 통계', '운동 종류', '횟수', 'description', 'count', color='blue', filename='exercise_chart.png')
    else:
        print("DataFrame is empty. No data to create chart.")

    return render_template('chart.html', chart_filename=chart_filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)