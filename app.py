from flask import Flask, render_template, Response
import cv2

app = Flask(__name__)

# Inicializa la cámara con índice 3
camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Codifica el frame en formato JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # Devuelve el frame como una respuesta de tipo 'multipart'
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def home():
    # Renderiza la página principal (layout con la barra lateral y el iframe)
    return render_template('layout.html', active_page='dashboard')

@app.route('/dashboard')
def dashboard():
    # Renderiza la vista del dashboard que se carga dentro del iframe
    return render_template('dashboard.html')

@app.route('/pepper')
def pepper():
    return render_template('pepper.html', active_page='pepper')

@app.route('/robot_arm')
def robot_arm():
    return render_template('robot_arm.html', active_page='robot_arm')

@app.route('/robot_dog')
def robot_dog():
    return render_template('robot_dog.html', active_page='robot_dog')

@app.route('/reservations')
def reservations():
    # Renderiza la vista de reservas
    return render_template('reservations.html', active_page='reservations')

@app.route('/video_feed3')
def video_feed3():
    # Servicio que devuelve el flujo de video de la cámara
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8065)
