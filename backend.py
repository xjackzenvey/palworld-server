from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify,render_template, session, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
import subprocess
import os
import shutil
import time
import atexit
from concurrent.futures import ThreadPoolExecutor


app = Flask(
    import_name     = __name__,
    template_folder = 'web',
    static_folder   = 'web/static',
    static_url_path = '/static',
)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'helloworldKey'

# 任务队列
task_status = {}

# 创建线程池执行器
executor = ThreadPoolExecutor(20)
atexit.register(executor.shutdown, wait=True)



# 数据库
db = SQLAlchemy(app)

# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    
    def __repr__(self):
        return f'<User {self.username}>'
    

# 用于注册新用户的 API
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': '用户名和密码是必填字段'}), 400
    
    username = data['username']
    password = data['password']
    
    # 检查用户名是否存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'message': '用户名已存在'}), 400
    
    # 创建新用户
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    # 建立用户文件夹
    os.makedirs(os.path.join("instance",'userdata',username), exist_ok=True)
    
    return jsonify({'message': '用户注册成功'}), 201


# 用于用户登录的 API
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': '用户名和密码是必填字段'}), 400
    
    username = data['username']
    password = data['password']
    
    # 查找用户
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': '用户名或密码错误'}), 401
    
    # 登录成功，设置 session
    session['user_id'] = user.id
    session['username'] = user.username
    session['login']   = True
    
    return jsonify({'message': '登录成功', 'user_id': user.id}), 200

# 用于用户登出的 API
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('login', None)
    
    return redirect(url_for('login_page'))


# 在后台线程中启动服务器
def start_server_in_background(args):
    
    task_id, username = args[0], args[1]
    
    try:
        # 启动服务器的批处理文件
        process = subprocess.Popen(['launch.bat'], cwd=os.path.join('instance','userdata',username,'game'), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 模拟启动时间
        time.sleep(10)
        
        # 检查服务器是否成功启动
        if process.poll() is None:  # 如果进程仍在运行
            task_status[task_id] = {'status': 'success', 'message': '服务器已启动'}
        else:
            task_status[task_id] = {'status': 'failed', 'message': '服务器启动失败'}
    
    except Exception as e:
        task_status[task_id] = {'status': 'failed', 'message': f'服务器启动失败: {str(e)}'}


# 用于启动服务器的 API
@app.route('/api/launchserver', methods=['POST'])
def launch_server():
    if 'login' not in session or not session['login']:
        return redirect(url_for('login_page'))
    
    try:
        # 生成任务ID
        task_id = int(time.time() * 1000)
        task_status[task_id] = {'status': 'pending', 'message': '服务器启动中...'}
        
        # 在后台线程中启动服务器
        executor.submit(start_server_in_background, [task_id,session['username']])
        
        return jsonify({
            'message': '服务器启动中...',
            'success': True,
            'task_id': task_id
        })
    
    except Exception as e:
        return jsonify({
            'message': f'服务器启动失败: {str(e)}',
            'success': False
        }), 500


# 与启动服务器一起，查询启动状态的 API
@app.route('/api/launchstatus/<int:task_id>', methods=['GET'])
def launch_status(task_id):
    if 'login' not in session or not session['login']:
        return redirect(url_for('login_page'))
    
    status = task_status.get(task_id)
    
    if not status:
        return jsonify({'message': '任务ID不存在', 'success': False}), 404
    
    status = task_status[task_id]
    
    return jsonify({
        'message': status['message'],
        'status': status['status'],
        'success': True
    })


# 用于安装服务器的 API
@app.route('/api/installserver', methods=['POST'])
def install_server():
    if 'login' not in session or not session['login']:
        return redirect(url_for('login_page'))
    
    # 安装服务器的逻辑
    shutil.copytree(os.path.join('instance', 'userdata', 'admin', 'game'), os.path.join('instance', 'userdata', session['username'], 'game'), dirs_exist_ok=True)
    
    return jsonify({'message': '服务器安装成功'}), 200




# 主页路由
@app.route('/')
def index_page():
    if 'login' not in session or not session['login']:
        return redirect(url_for('login_page'))
    
    return render_template('index.html')


# 登录页面路由
@app.route('/login')
def login_page():
    if 'login' in session and session['login']:
        return render_template('index.html')
    
    return render_template('login.html')


# 注册页面路由
@app.route('/register')
def register_page():
    if 'login' in session and session['login']:
        return render_template('index.html')
    
    return render_template('register.html')

# 存档页面路由
@app.route('/saves')
def saves_page():
    if 'login' not in session or not session['login']:
        return redirect(url_for('login_page'))
    
    return render_template('saves.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)