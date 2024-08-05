from flask import Flask, session, request, redirect, url_for, render_template, flash
from flask_session import Session
import mysql.connector
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
            cursor = db.cursor()
            cursor.execute("SELECT * FROM user WHERE username = %s", (user_id,))
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
        cursor = db.cursor()
        cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user[3], password):
            session['id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('main'))
        else:
            flash('로그인 실패')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('id', None)
    session.pop('username', None)
    session.pop('password', None)
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
    
    cursor.execute("SELECT * FROM memos WHERE user_id = %s AND date = %s", (session['user_id'], date))
    existing_memo = cursor.fetchone()
    
    if existing_memo:
        cursor.execute("UPDATE memos SET memo = %s WHERE user_id = %s AND date = %s", (memo_text, session['user_id'], date))
    else:
        cursor.execute("INSERT INTO memos (user_id, date, memo) VALUES (%s, %s, %s)", (session['user_id'], date, memo_text))
    
    db.commit()
    cursor.close()
    db.close()
    
    year, month, day = map(int, date.split('-'))
    return redirect(url_for('main', year=year, month=month, day=day))

@app.route('/delete_memo', methods=['POST'])
def delete_memo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    date = request.form['date']
    
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM memos WHERE user_id = %s AND date = %s", (session['user_id'], date))
    existing_memo = cursor.fetchone()
    
    if existing_memo:
        cursor.execute("DELETE FROM memos WHERE user_id = %s AND date = %s", (session['user_id'], date))
        
    db.commit()
    cursor.close()
    db.close()
    
    year, month, day = map(int, date.split('-'))
    return redirect(url_for('main', year=year, month=month, day=day))
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)