from flask import Flask, session, request, redirect, url_for, render_template, flash
from flask_session import Session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import calendar
from datetime import datetime
from gpt import ask_chatgpt

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

exercise_map = {
    "upper_body": "상체 전체 운동",
    "chest": "가슴 운동",
    "back": "등 운동",
    "shoulder": "어깨 운동",
    "arm": "팔 전체 운동",
    "bicep": "이두 운동",
    "tricep": "삼두 운동",
    "lower_body": "하체 운동"
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

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
            cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                flash('아이디 중복')
                cursor.close()
                db.close()
                return redirect(url_for('signup'))
            
            cursor.execute("INSERT INTO user (username, user_id, password, email, phone, birth, gender, height, weight) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (username, user_id, hashed_password, email, phone, birth, gender, height, weight))
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
        cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
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
    
    cursor.execute("SELECT exercise_type FROM exercises WHERE user_id = %s AND date = %s", (user_id, date))
    exercises = cursor.fetchone()
    
    cursor.execute("SELECT * FROM memos WHERE user_id = %s AND date = %s AND exercise_type", (user_id, date))
    memos = cursor.fetchall()
    
    cursor.execute("SELECT recommendation FROM exercise_recommendations WHERE user_id = %s AND date = %s ORDER BY id DESC LIMIT 1", (user_id, date))
    recommendation = cursor.fetchone()
    chatgpt_recommendation = recommendation['recommendation'] if recommendation else None
    
    cursor.close()
    db.close()
    
    year, month, day = map(int, date.split('-'))
    return render_template('memo.html', year=year, month=month, day=day, exercises=exercises, memos=memos, chatgpt_recommendation=chatgpt_recommendation, exercise_map=exercise_map)

@app.route('/update_exercise', methods=['POST'])
def update_exercise():
    if 'id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['id']
    date = request.form['date']
    
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute("DELETE FROM exercises WHERE user_id = %s AND date = %s", (user_id, date))
    cursor.execute("DELETE FROM memos WHERE user_id = %s AND date = %s", (user_id, date))
    
    exercises = [request.form.get(f'exercise{i}', '') for i in range(1, 4)]
    cursor.execute("INSERT INTO exercises (user_id, date, exercise1, exercise2, exercise3) VALUES (%s, %s, %s, %s, %s)", 
                   (user_id, date, exercises[0], exercises[1], exercises[2]))
    
    for exercise_number in range(1, 4):
        for memo_id in range(5):
            exercise_name = request.form.get(f'exercise_name{exercise_number}_{memo_id}')
            exercise_set = request.form.get(f'exercise_set{exercise_number}_{memo_id}')
            exercise_weight = request.form.get(f'exercise_weight{exercise_number}_{memo_id}')
            
            if exercise_name:
                cursor.execute("INSERT INTO memos (user_id, date, exercise_number, memo_id, exercise_name, exercise_set, exercise_weight) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                               (user_id, date, exercise_number, memo_id, exercise_name, exercise_set, exercise_weight))
    
    db.commit()
    cursor.close()
    db.close()
    
    flash('저장 되었습니다.')
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
    
    cursor.execute("DELETE FROM exercises WHERE user_id = %s AND date = %s", (user_id, date))
    cursor.execute("DELETE FROM memos WHERE user_id = %s AND date = %s", (user_id, date))
    
    db.commit()
    cursor.close()
    db.close()
    
    flash('삭제 되었습니다.')
    year, month, day = map(int, date.split('-'))
    return redirect(url_for('memo', year=year, month=month, day=day))

@app.route('/gpt_show', methods=['GET','POST'])
def gpt_show():
    if 'id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['id']
    date = request.form['date']
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT birth, gender, height, weight FROM user WHERE id = %s", (user_id,))
    user_info = cursor.fetchone()
    
    # cursor.execute("SELECT exercise_name, exercise_set, exercise_weight FROM memos WHERE user_id = %s AND date = %s", (user_id, date))
    # memo_info = cursor.fetchone()
    
    cursor.execute("SELECT exercise1, exercise2, exercise3 FROM exercises WHERE user_id = %s AND date = %s", (user_id, date))
    exercise_info = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    if not exercise_info:
        flash('선택된 운동이 없습니다.')
        year, month, day = map(int, date.split('-'))
        return redirect(url_for('memo', year=year, month=month, day=day))
    
    prompt = f"사용자 정보: 생년월일 {user_info['birth']}, 성별 {user_info['gender']}, 키 {user_info['height']}cm, 체중 {user_info['weight']}kg\n"
    prompt += f"선택한 운동: {exercise_info['exercise1']}, {exercise_info['exercise2']}, {exercise_info['exercise3']}\n"
    # if memo_info:
    #     prompt += f"오늘의 운동 기록: {memo_info['exercise_name']} {memo_info['exercise_set']}세트 {memo_info['exercise_weight']}kg\n"
    prompt += "위 선택한 운동에 맞는 운동 종목 3가지씩 세트수랑 무게를 사용자 정보에 맞게 추천해줘."

    recommendation = ask_chatgpt(prompt)

    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute("INSERT INTO exercise_recommendations (user_id, date, recommendation) VALUES (%s, %s, %s)", (user_id, date, recommendation))
    db.commit()
    
    cursor.close()
    db.close()

    year, month, day = map(int, date.split('-'))
    return redirect(url_for('memo', year=year, month=month, day=day))
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)