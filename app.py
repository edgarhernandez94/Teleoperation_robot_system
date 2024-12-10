from flask import Flask, render_template, Response, redirect, url_for, request, session, flash
import cv2
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask import jsonify
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from collections import Counter

# Conexión a MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['teleoperation_system']  # Nombre de la base de datos
users_collection = db['users']  # Nombre de la colección
reservations_collection = db['reservations']  # Crearás esta colección al insertar el primer documento


app = Flask(__name__)
app.secret_key = 'un_clave_secreto_muy_segura'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # ruta para login
login_manager.login_message = 'Please log in to access this page.'

# Clase User para flask-login
class User(UserMixin):
    def __init__(self, id_, username):
        self.id = id_
        self.username = username

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(id_=user['id'], username=user['username'])
    return None

def create_users_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    ''')
    conn.commit()
    conn.close()

create_users_table()

camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('layout.html', active_page='dashboard')
    else:
        return redirect(url_for('login'))

from werkzeug.security import check_password_hash
from flask_login import login_user

from werkzeug.security import check_password_hash
from flask_login import login_user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Buscar usuario en la colección
        user = users_collection.find_one({"username": username})
        if user and check_password_hash(user['password'], password):
            # Crear una instancia de User para login_user
            user_obj = User(str(user['_id']), user['username'])
            user_obj.first_name = user.get('first_name', '')  # Obtener el nombre si existe
            login_user(user_obj)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        occupation = request.form['occupation']
        company = request.form['company']
        country = request.form['country']
        role = request.form['role']

        # Verificar si ya existe el usuario
        if users_collection.find_one({"username": username}):
            flash('Username already exists. Choose another.')
            return redirect(url_for('register'))

        # Crear el documento del usuario
        user_data = {
            "username": username,
            "password": generate_password_hash(password),
            "first_name": first_name,
            "last_name": last_name,
            "occupation": occupation,
            "company": company,
            "country": country,
            "role": role
        }

        # Insertar el usuario en MongoDB
        users_collection.insert_one(user_data)
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

from collections import Counter

from collections import Counter

from collections import Counter

@app.route('/dashboard')
@login_required
def dashboard():
    now = datetime.now()
    # Obtener la próxima reserva
    next_reservation = reservations_collection.find_one({
        "user_id": ObjectId(current_user.id),
        "start_datetime": {"$gte": now}
    }, sort=[("start_datetime", 1)])
    
    if next_reservation:
        next_date_str = next_reservation['start_datetime'].strftime("%d %b %Y, %I:%M %p")
        next_robot = next_reservation['robot']
    else:
        next_date_str = "No upcoming sessions"
        next_robot = ""

    # Obtener todas las sesiones del usuario actual
    sessions = list(reservations_collection.find({"user_id": ObjectId(current_user.id)}))

    # Agrupar sesiones por robot y fecha
    def get_sessions_by_robot(robot_name):
        return [s["start_datetime"].strftime("%Y-%m-%d") for s in sessions if s["robot"] == robot_name]

    arm_sessions = get_sessions_by_robot("arm-robot")
    pepper_sessions = get_sessions_by_robot("pepper-avatar")
    dog_sessions = get_sessions_by_robot("dog-robot")

    # Contar sesiones por fecha
    def count_sessions_by_date(sessions):
        return Counter(sessions)

    arm_sessions_count = dict(count_sessions_by_date(arm_sessions) or {})
    pepper_sessions_count = dict(count_sessions_by_date(pepper_sessions) or {})
    dog_sessions_count = dict(count_sessions_by_date(dog_sessions) or {})

    # Continuar con la lógica existente para el uso y duración
    pipeline = [
        {"$match": {"user_id": ObjectId(current_user.id)}},
        {"$group": {"_id": "$robot", "total_duration": {"$sum": "$duration"}, "count_sessions": {"$sum": 1}}}
    ]

    usage_data = list(reservations_collection.aggregate(pipeline))

    usage_map = {
        "arm-robot": {"duration": 0, "count": 0},
        "pepper-avatar": {"duration": 0, "count": 0},
        "dog-robot": {"duration": 0, "count": 0}
    }

    for doc in usage_data:
        usage_map[doc['_id']]['duration'] = doc['total_duration']
        usage_map[doc['_id']]['count'] = doc['count_sessions']

    # Asignar datos para cada robot
    arm_usage = usage_map["arm-robot"]["duration"]
    pepper_usage = usage_map["pepper-avatar"]["duration"]
    dog_usage = usage_map["dog-robot"]["duration"]

    arm_count = usage_map["arm-robot"]["count"]
    pepper_count = usage_map["pepper-avatar"]["count"]
    dog_count = usage_map["dog-robot"]["count"]
    robot_tasks_count = {
    "Arm Robot": 5,
    "Pepper Robot Avatar": 3,
    "Dog Robot": 2
}
    return render_template(
        'dashboard.html',
        next_date_str=next_date_str,
        next_robot=next_robot,
        arm_usage=arm_usage,
        pepper_usage=pepper_usage,
        dog_usage=dog_usage,
        arm_count=arm_count,
        pepper_count=pepper_count,
        dog_count=dog_count,
        arm_sessions_count=arm_sessions_count,  # Contar por fecha
        pepper_sessions_count=pepper_sessions_count,
        dog_sessions_count=dog_sessions_count,
        robot_tasks_count=robot_tasks_count,  # Add this line
        )

@app.route('/pepper')
@login_required
def pepper():
    return render_template('pepper.html', active_page='pepper')

@app.route('/robot_arm')
@login_required
def robot_arm():
    return render_template('robot_arm.html', active_page='robot_arm')

@app.route('/robot_dog')
@login_required
def robot_dog():
    return render_template('robot_dog.html', active_page='robot_dog')

@app.route('/reservations')
@login_required
def reservations():
    now = datetime.now()
    user_reservations = list(reservations_collection.find({"user_id": ObjectId(current_user.id)}))
    user_reservations.sort(key=lambda r: r['start_datetime'])
    
    upcoming_reservations = [r for r in user_reservations if r['start_datetime'] >= now]
    past_reservations = [r for r in user_reservations if r['start_datetime'] < now]

    # Si usas check_availability, también asegúrate de definir occupied_spots, checked_robot y checked_date
    # antes de renderizar, por ejemplo:
    occupied_spots = []
    checked_robot = None
    checked_date = None

    return render_template(
        'reservations.html',
        active_page='reservations',
        upcoming_reservations=upcoming_reservations,
        past_reservations=past_reservations,
        occupied_spots=occupied_spots,
        checked_robot=checked_robot,
        checked_date=checked_date
    )


@app.route('/make_reservation', methods=['POST'])
@login_required
def make_reservation():
    robot = request.form['robot']
    date_str = request.form['date']
    time_str = request.form['time']
    duration_str = request.form['duration']

    # Convertir fecha/hora
    start = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')

    # Determinar duración en minutos
    if duration_str == '30 minutes':
        dur_minutes = 30
    elif duration_str == '1 hour':
        dur_minutes = 60
    elif duration_str == '2 hours':
        dur_minutes = 120
    else:
        dur_minutes = 30

    end = start + timedelta(minutes=dur_minutes)

    # Verificar si ya existe una reserva para ese robot que se solape
    # Criterio: buscar cualquier reserva del mismo robot donde:
    # existing_start < end AND existing_end > start
    existing = reservations_collection.find_one({
        "robot": robot,
        "$or": [
            {
                # Caso 1: Inicio existente antes del fin nuevo y fin existente después del inicio nuevo
                "start_datetime": {"$lt": end}
            },
            # Podemos revisar si hace falta más condiciones
        ]
    })

    # Necesitamos filtrar aún más las reservas encontradas:
    # Mejor usar un pipeline para filtrar con más detalle o hacerlo en Python:
    # Usamos el match inicial, luego filtramos en Python si existe realmente solapamiento.
    # Para ello, tendremos que calcular el end de la reserva existente:
    
    overlapping_reservation = None
    for res in reservations_collection.find({"robot": robot}):
        existing_start = res['start_datetime']
        existing_end = existing_start + timedelta(minutes=res['duration'])

        # Verificar solapamiento:
        if existing_start < end and existing_end > start:
            # Hay solapamiento
            overlapping_reservation = res
            break

    if overlapping_reservation:
        flash("This robot is already reserved at this time. Please choose another time or robot.")
        return redirect(url_for('reservations'))

    # Si no hay solapamiento, insertar la nueva reserva
    reservation_data = {
        "user_id": ObjectId(current_user.id),
        "robot": robot,
        "start_datetime": start,
        "duration": dur_minutes
    }

    reservations_collection.insert_one(reservation_data)
    flash("Reservation successfully made!")
    return redirect(url_for('reservations'))
@app.route('/check_availability', methods=['POST'])
@login_required
def check_availability():
    robot = request.form['robot']
    date_str = request.form['date']

    if not date_str or not robot:
        flash("Please select a robot and a date.")
        return redirect(url_for('reservations'))

    # Obtener todas las reservas del usuario para mantener consistencia en la plantilla
    now = datetime.now()
    user_reservations = list(reservations_collection.find({"user_id": ObjectId(current_user.id)}))
    user_reservations.sort(key=lambda r: r['start_datetime'])
    upcoming_reservations = [r for r in user_reservations if r['start_datetime'] >= now]
    past_reservations = [r for r in user_reservations if r['start_datetime'] < now]

    # Filtrar reservas del robot en la fecha dada (para mostrar ocupadas)
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    next_day = date_obj + timedelta(days=1)
    query = {
        "robot": robot,
        "start_datetime": {"$gte": date_obj, "$lt": next_day}
    }
    daily_reservations = list(reservations_collection.find(query))

    occupied_spots = []
    for res in daily_reservations:
        start = res['start_datetime']
        end = start + timedelta(minutes=res['duration'])
        occupied_spots.append(f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}")

    return render_template('reservations.html',
                           active_page='reservations',
                           upcoming_reservations=upcoming_reservations,
                           past_reservations=past_reservations,
                           occupied_spots=occupied_spots,
                           checked_robot=robot,
                           checked_date=date_str)

@app.route('/delete_reservation/<reservation_id>', methods=['POST'])
@login_required
def delete_reservation(reservation_id):
    from bson.objectid import ObjectId
    
    # Buscamos la reserva para asegurarnos que pertenece al usuario actual
    res = reservations_collection.find_one({"_id": ObjectId(reservation_id), "user_id": ObjectId(current_user.id)})
    if not res:
        flash("Reservation not found or does not belong to you.")
        return redirect(url_for('reservations'))
    
    # Eliminar la reserva
    reservations_collection.delete_one({"_id": ObjectId(reservation_id)})
    flash("Reservation deleted successfully!")
    return redirect(url_for('reservations'))

@app.route('/video_feed3')
@login_required
def video_feed3():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
@login_manager.user_loader
def load_user(user_id):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        user_obj = User(str(user['_id']), user['username'])
        user_obj.first_name = user.get('first_name', '')
        return user_obj
    return None

@app.route('/log_time', methods=['POST'])
@login_required
def log_time():
    data = request.get_json()
    page = data.get('page')
    elapsed_time = data.get('elapsed_time')

    # Guardar en MongoDB
    db['user_activity'].insert_one({
        "user_id": ObjectId(current_user.id),
        "page": page,
        "elapsed_time": elapsed_time,
        "timestamp": datetime.now()
    })
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8065, debug=True)
