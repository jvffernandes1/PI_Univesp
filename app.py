from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from bson.objectid import ObjectId

app = Flask(__name__)

# Configuração correta do MongoDB Atlas
app.config[
    'MONGO_URI'] = "mongodb+srv://piunivesp:n6nOL31JSFoUDsnX@clusterpi.rxd1i.mongodb.net/restaurants_db?retryWrites=true&w=majority&appName=clusterPI"
app.config['SECRET_KEY'] = 'minha_chave_super_secreta'

# Inicializar o PyMongo corretamente
mongo = PyMongo(app)
db = mongo.db  # Armazena a referência do banco de dados

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, user_id, name, email, is_admin=False):
        self.id = user_id
        self.name = name
        self.email = email
        self.is_admin = is_admin


@login_manager.user_loader
def load_user(user_id):
    user_data = db.users.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(str(user_data['_id']), user_data['name'], user_data['email'], user_data.get('is_admin', False))
    return None



@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        # Verifica se o usuário já existe
        if db.users.find_one({'email': email}):
            flash('Email já cadastrado!', 'danger')
            return redirect(url_for('register'))

        # Define o primeiro usuário como admin automaticamente
        is_admin = db.users.count_documents({}) == 0

        user_id = db.users.insert_one({
            'name': name,
            'email': email,
            'password': password,
            'is_admin': is_admin
        }).inserted_id

        user = User(str(user_id), name, email)
        login_user(user)
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/admin_panel')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('home'))

    users = db.users.find()
    return render_template('admin_panel.html', users=users)

@app.route('/promote_user/<user_id>')
@login_required
def promote_user(user_id):
    if not current_user.is_admin:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('home'))

    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'is_admin': True}})
    flash('Usuário promovido a administrador!', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/add_restaurant', methods=['GET', 'POST'])
@login_required
def add_restaurant():
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página!', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        price_range = request.form['price_range']
        category = request.form['category']
        website = request.form['website']

        db.restaurants.insert_one({
            'name': name,
            'address': address,
            'price_range': price_range,
            'category': category,
            'website': website
        })

        flash('Restaurante cadastrado com sucesso!', 'success')
        return redirect(url_for('home'))

    return render_template('add_restaurant.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_data = db.users.find_one({'email': email})

        if user_data and check_password_hash(user_data['password'], password):
            user = User(str(user_data['_id']), user_data['name'], user_data['email'])
            login_user(user)
            return redirect(url_for('home'))

        flash('Credenciais inválidas!', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
