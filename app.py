import os
from flask import Flask, render_template, redirect, url_for, send_from_directory, request
from flask_wtf import FlaskForm, CSRFProtect
from werkzeug.utils import secure_filename
from wtforms import StringField, FileField, DateField, TimeField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired, Email
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'this_should_be_random_and_secure'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB per file

csrf = CSRFProtect(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_db():
    with sqlite3.connect("database.db") as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            tanggal TEXT NOT NULL,
            waktu_pengambilan TEXT,
            gambar_utama TEXT NOT NULL,
            gambar_tambahan TEXT
        )""")

class ChecklistForm(FlaskForm):
    name = StringField("Nama", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    tanggal = DateField("Tanggal", validators=[DataRequired()])
    waktu_pengambilan = TimeField("Waktu Pengambilan")
    gambar_utama = FileField("Gambar Utama", validators=[DataRequired()])
    gambar_tambahan = MultipleFileField("Gambar Tambahan")
    submit = SubmitField("Simpan")

@app.route("/form", methods=["GET", "POST"])
def form():
    form = ChecklistForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        tanggal = form.tanggal.data.isoformat()
        waktu = form.waktu_pengambilan.data.isoformat() if form.waktu_pengambilan.data else None

        # Upload gambar utama
        file_main = form.gambar_utama.data
        filename_main = secure_filename(file_main.filename)
        path_main = os.path.join(app.config['UPLOAD_FOLDER'], filename_main)
        file_main.save(path_main)

        # Upload gambar tambahan
        filenames_additional = []
        for file in form.gambar_tambahan.data:
            if file and file.filename:
                fname = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                filenames_additional.append(fname)

        # Simpan ke database
        with sqlite3.connect("database.db") as conn:
            conn.execute("""INSERT INTO uploads 
                (name, email, tanggal, waktu_pengambilan, gambar_utama, gambar_tambahan)
                VALUES (?, ?, ?, ?, ?, ?)""", 
                (name, email, tanggal, waktu, filename_main, ','.join(filenames_additional)))
        return redirect(url_for('data'))

    return render_template("form_flaskform.html", form=form)

@app.route("/data")
def data():
    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM uploads ORDER BY id DESC").fetchall()
    return render_template("data_flaskform.html", data=rows)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
