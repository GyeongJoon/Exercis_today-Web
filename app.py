from flask import Flask, session, request, redirect, url_for, render_template, jsonify
from flask_session import Session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
import calendar
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'joon'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# MySQL 연결 설정
db_config = {
    'user': 'joon',
    'password': '1234',
    'host': 'localhost',
    'database': 'backend'
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
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO user (username, password) VALUES (%s, %s)", (username, hashed_password))
        db.commit()
        cursor.close()
        db.close()

        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM user WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('main'))
        else:
            return 'Invalid credentials'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/main')
def main():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    year = request.args.get('year', type=int, default=datetime.now().year)
    month = request.args.get('month', type=int, default=datetime.now().month)
    
    # 달력 정보 생성
    cal = calendar.monthcalendar(year, month)
    
    # 이전 달과 다음 달 계산
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
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    date = f"{year}-{month:02d}-{day:02d}"
    
    user_id = session['user_id']
    
    # 데이터베이스에서 해당 날짜의 메모를 가져옵니다
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM memos WHERE user_id = %s AND date = %s", (user_id, date))
    memo = cursor.fetchone()
    cursor.close()
    db.close()
    
    return render_template('memo.html', year=year, month=month, day=day, memo=memo)

@app.route('/update_memo', methods=['POST'])
def update_memo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    date = request.form['date']
    memo_text = request.form['memo']
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # 메모가 이미 존재하는지 확인
    cursor.execute("SELECT * FROM memos WHERE user_id = %s AND date = %s", (session['user_id'], date))
    existing_memo = cursor.fetchone()
    
    if existing_memo:
        # 메모가 존재하면 업데이트
        cursor.execute("UPDATE memos SET memo = %s WHERE user_id = %s AND date = %s", (memo_text, session['user_id'], date))
    else:
        # 메모가 없으면 새로 삽입
        cursor.execute("INSERT INTO memos (user_id, date, memo) VALUES (%s, %s, %s)", (session['user_id'], date, memo_text))
    
    db.commit()
    cursor.close()
    db.close()
    
    year, month, day = map(int, date.split('-'))
    return redirect(url_for('memo', year=year, month=month, day=day))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)