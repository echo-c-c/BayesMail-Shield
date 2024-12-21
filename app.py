from flask import Flask, request, jsonify, send_from_directory, session
import joblib
import os
from predict import predict_label
import numpy as np
import jieba
import mysql.connector
from config import MYSQL_CONFIG
import hashlib
from functools import wraps
from flask_cors import CORS
from datetime import timedelta

# 定义自定义的CountVectorizer类
class CountVectorizer:
    def __init__(self, *, vocabulary=None, ngram_range=(1, 1), stop_words=None):
        self.vocabulary = vocabulary
        self.ngram_range = ngram_range
        self.stop_words = stop_words

    def fit_transform(self, texts):
        self.vocabulary_ = {}
        self.index_ = {}
        index = 0
        for text in texts:
            ngrams = self._get_ngrams(text)
            for ngram in ngrams:
                if self.vocabulary is not None and ngram not in self.vocabulary:
                    continue
                if ngram not in self.vocabulary_:
                    self.vocabulary_[ngram] = index
                    self.index_[index] = ngram
                    index += 1

        matrix = np.zeros((len(texts), len(self.vocabulary_)), dtype=int)
        for i, text in enumerate(texts):
            ngrams = self._get_ngrams(text)
            for ngram in ngrams:
                if ngram in self.vocabulary_:
                    j = self.vocabulary_[ngram]
                    matrix[i][j] += 1
        return matrix

    def transform(self, texts):
        matrix = np.zeros((len(texts), len(self.vocabulary_)), dtype=int)
        for i, text in enumerate(texts):
            ngrams = self._get_ngrams(text)
            for ngram in ngrams:
                if ngram in self.vocabulary_:
                    j = self.vocabulary_[ngram]
                    matrix[i][j] += 1
        return matrix

    def _get_ngrams(self, text):
        try:
            words = list(jieba.cut(text))
        except:
            words =['']
        if self.stop_words is not None:
            words = [word for word in words if word not in self.stop_words]

        ngrams = []
        min_n, max_n = self.ngram_range
        for n in range(min_n, max_n + 1):
            for i in range(len(words) - n + 1):
                ngram = ' '.join(words[i:i + n])
                ngrams.append(ngram)
        return ngrams

class TfidfVectorizer(CountVectorizer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.idf_ = None

    def fit_transform(self, texts):
        tf_matrix = super().fit_transform(texts)
        self.idf_ = np.log((1 + len(texts)) / (1 + np.sum(tf_matrix > 0, axis=0))) + 1
        tfidf_matrix = tf_matrix * self.idf_
        row_norms = np.linalg.norm(tfidf_matrix, axis=1, keepdims=True)
        tfidf_matrix = tfidf_matrix / np.where(row_norms == 0, 1, row_norms)
        return tfidf_matrix

    def transform(self, texts):
        tf_matrix = super().transform(texts)
        tfidf_matrix = tf_matrix * self.idf_ if self.idf_ is not None else tf_matrix
        row_norms = np.linalg.norm(tfidf_matrix, axis=1, keepdims=True)
        tfidf_matrix = tfidf_matrix / np.where(row_norms == 0, 1, row_norms)
        return tfidf_matrix

app = Flask(__name__)
CORS(app, supports_credentials=True)  # 允许跨域请求携带凭证
app.secret_key = os.urandom(24)  # 用于session加密
app.permanent_session_lifetime = timedelta(days=7)  # 设置session有效期为7天

# 数据库连接函数
def get_db():
    return mysql.connector.connect(**MYSQL_CONFIG)

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

# 提供静态文件服务
@app.route('/')
def index():
    return send_from_directory('邮箱', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('邮箱', path)

# 注册API
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': '请输入邮箱和密码'}), 400

    # 验证邮箱格式
    if not '@' in email or not '.' in email:
        return jsonify({'error': '请输入有效的邮箱地址'}), 400

    # 验证密码长度
    if len(password) < 6:
        return jsonify({'error': '密码长度至少为6位'}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 检查邮箱是否已存在
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': '该邮箱已被注册'}), 400
            
        # 密码加密
        hashed_password = hashlib.md5(password.encode()).hexdigest()
            
        # 插入新用户
        cursor.execute("""
            INSERT INTO users (email, password)
            VALUES (%s, %s)
        """, (email, hashed_password))
        
        conn.commit()
        
        # 获取新插入的用户ID
        user_id = cursor.lastrowid
        
        # 自动登录
        session['user_id'] = user_id
        session['email'] = email
        
        return jsonify({
            'message': '注册成功',
            'user': {
                'email': email
            }
        })
            
    finally:
        cursor.close()
        conn.close()

# 登录API
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': '请输入邮箱和密码'}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 密码加密
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        
        cursor.execute("""
            SELECT id, email FROM users 
            WHERE email = %s AND password = %s
        """, (email, hashed_password))
        
        user = cursor.fetchone()
        
        if user:
            session['user_id'] = user['id']
            session['email'] = user['email']
            return jsonify({
                'message': '登录成功',
                'user': {
                    'email': user['email']
                }
            })
        else:
            return jsonify({'error': '邮箱或密码错误'}), 401
            
    finally:
        cursor.close()
        conn.close()

# 获取用户信息API
@app.route('/api/user', methods=['GET'])
@login_required
def get_user():
    return jsonify({
        'email': session.get('email')
    })

# 邮件分类API
@app.route('/api/classify', methods=['POST'])
@login_required
def classify_email():
    data = request.json
    email_content = data.get('content', '')
    
    # 使用predict.py中的函数进行预测
    result = predict_label(email_content)
    
    return jsonify({
        'is_spam': result == '垃圾邮件',
        'message': result
    })

# 发送邮件API
@app.route('/api/send_email', methods=['POST'])
@login_required
def send_email():
    data = request.json
    receiver_email = data.get('to')
    subject = data.get('subject')
    content = data.get('content')

    if not all([receiver_email, subject, content]):
        return jsonify({'error': '请填写完整的邮件信息'}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        # 获取接收者ID
        cursor.execute("SELECT id FROM users WHERE email = %s", (receiver_email,))
        receiver = cursor.fetchone()
        if not receiver:
            return jsonify({'error': '收件人不存在'}), 404

        # 使用朴素贝叶斯模型预测是否为垃圾邮件
        is_spam = predict_label(content) == '垃圾邮件'

        # 插入邮件
        cursor.execute("""
            INSERT INTO emails (sender_id, receiver_id, subject, content, is_spam)
            VALUES (%s, %s, %s, %s, %s)
        """, (session['user_id'], receiver[0], subject, content, is_spam))

        conn.commit()
        return jsonify({'message': '邮件发送成功'})

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# 获取收件箱API
@app.route('/api/inbox', methods=['GET'])
@login_required
def get_inbox():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # 获取所有收到的邮件，包括垃圾邮件标记
        cursor.execute("""
            SELECT e.*, u.email as sender_email 
            FROM emails e
            JOIN users u ON e.sender_id = u.id
            WHERE e.receiver_id = %s AND e.is_spam = FALSE
            ORDER BY e.created_at DESC
        """, (session['user_id'],))

        emails = cursor.fetchall()
        return jsonify({'emails': emails})

    finally:
        cursor.close()
        conn.close()

# 获取垃圾邮件API
@app.route('/api/spam', methods=['GET'])
@login_required
def get_spam_emails():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT e.*, u.email as sender_email 
            FROM emails e
            JOIN users u ON e.sender_id = u.id
            WHERE e.receiver_id = %s AND e.is_spam = TRUE
            ORDER BY e.created_at DESC
        """, (session['user_id'],))

        emails = cursor.fetchall()
        return jsonify({'emails': emails})

    finally:
        cursor.close()
        conn.close()

# 获取已发送邮件API
@app.route('/api/sent', methods=['GET'])
@login_required
def get_sent_emails():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT e.*, u.email as receiver_email 
            FROM emails e
            JOIN users u ON e.receiver_id = u.id
            WHERE e.sender_id = %s
            ORDER BY e.created_at DESC
        """, (session['user_id'],))

        emails = cursor.fetchall()
        return jsonify({'emails': emails})

    finally:
        cursor.close()
        conn.close()

# 退出登录API
@app.route('/api/logout', methods=['POST'])
def logout():
    # 清除session中的用户信息
    session.clear()
    return jsonify({'message': '退出成功'})

# 获取用户列表接口
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # 获取所有用户的邮箱
        cursor.execute("SELECT email FROM users")
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 获取邮件详情API
@app.route('/api/email/<int:email_id>', methods=['GET'])
@login_required
def get_email(email_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # 获取邮件详情，同时获取发件人和收件人的邮箱
        cursor.execute("""
            SELECT e.*, 
                   sender.email as sender_email,
                   receiver.email as receiver_email,
                   e.created_at as date
            FROM emails e
            JOIN users sender ON e.sender_id = sender.id
            JOIN users receiver ON e.receiver_id = receiver.id
            WHERE e.id = %s AND (e.sender_id = %s OR e.receiver_id = %s)
        """, (email_id, session['user_id'], session['user_id']))

        email = cursor.fetchone()
        
        if not email:
            return jsonify({'error': '邮件不存在或无权限查看'}), 404

        return jsonify(email)

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000) 