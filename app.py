from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from bson.objectid import ObjectId
from datetime import datetime

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

@app.route('/restaurantes')
def restaurantes():
    # Busca todos os restaurantes no banco de dados
    restaurantes = list(db.restaurants.find())
    
    # Para cada restaurante, calcula a média das avaliações
    for restaurante in restaurantes:
        avaliacoes = list(db.ratings.find({'restaurant_id': restaurante['_id']}))
        if avaliacoes:
            media = sum(av['rating'] for av in avaliacoes) / len(avaliacoes)
            restaurante['media_avaliacoes'] = round(media, 1)
            restaurante['total_avaliacoes'] = len(avaliacoes)
        else:
            restaurante['media_avaliacoes'] = 0
            restaurante['total_avaliacoes'] = 0
            
        # Verifica se o usuário atual já avaliou este restaurante
        if current_user.is_authenticated:
            avaliacao_usuario = db.ratings.find_one({
                'restaurant_id': restaurante['_id'],
                'user_id': ObjectId(current_user.id)
            })
            restaurante['avaliacao_usuario'] = avaliacao_usuario['rating'] if avaliacao_usuario else None
    
    return render_template('restaurantes.html', restaurantes=restaurantes)

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
    restaurantes = list(db.restaurants.find())
    return render_template('admin_panel.html', users=users, restaurantes=restaurantes)

@app.route('/promote_user/<user_id>')
@login_required
def promote_user(user_id):
    if not current_user.is_admin:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('home'))

    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'is_admin': True}})
    flash('Usuário promovido a administrador!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/remove_admin/<user_id>')
@login_required
def remove_admin(user_id):
    if not current_user.is_admin:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('home'))

    # Não permite remover o próprio status de admin
    if user_id == current_user.id:
        flash('Você não pode remover seu próprio status de administrador!', 'danger')
        return redirect(url_for('admin_panel'))
    
    # Busca o usuário a ser removido
    user_to_remove = db.users.find_one({'_id': ObjectId(user_id)})
    if not user_to_remove:
        flash('Usuário não encontrado!', 'danger')
        return redirect(url_for('admin_panel'))
    
    # Verifica se é o primeiro usuário (dono do sistema)
    first_user = db.users.find_one(sort=[('_id', 1)])
    if user_to_remove['_id'] == first_user['_id']:
        flash('Não é possível remover o status de administrador do dono do sistema!', 'danger')
        return redirect(url_for('admin_panel'))
    
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'is_admin': False}})
    flash('Status de administrador removido com sucesso!', 'success')
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

@app.route('/avaliar/<restaurant_id>', methods=['POST'])
@login_required
def avaliar_restaurante(restaurant_id):
    rating = int(request.form.get('rating'))
    if not 1 <= rating <= 5:
        flash('Avaliação deve ser entre 1 e 5!', 'danger')
        return redirect(url_for('restaurantes'))
    
    # Verifica se o usuário já avaliou este restaurante
    avaliacao_existente = db.ratings.find_one({
        'restaurant_id': ObjectId(restaurant_id),
        'user_id': ObjectId(current_user.id)
    })
    
    if avaliacao_existente:
        # Atualiza a avaliação existente
        db.ratings.update_one(
            {'_id': avaliacao_existente['_id']},
            {'$set': {'rating': rating, 'updated_at': datetime.utcnow()}}
        )
    else:
        # Cria uma nova avaliação
        db.ratings.insert_one({
            'restaurant_id': ObjectId(restaurant_id),
            'user_id': ObjectId(current_user.id),
            'rating': rating,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
    
    flash('Avaliação registrada com sucesso!', 'success')
    return redirect(url_for('restaurantes'))

@app.route('/editar_restaurante/<restaurant_id>', methods=['GET', 'POST'])
@login_required
def editar_restaurante(restaurant_id):
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página!', 'danger')
        return redirect(url_for('home'))

    restaurante = db.restaurants.find_one({'_id': ObjectId(restaurant_id)})
    if not restaurante:
        flash('Restaurante não encontrado!', 'danger')
        return redirect(url_for('restaurantes'))

    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        price_range = request.form['price_range']
        category = request.form['category']
        website = request.form['website']

        db.restaurants.update_one(
            {'_id': ObjectId(restaurant_id)},
            {'$set': {
                'name': name,
                'address': address,
                'price_range': price_range,
                'category': category,
                'website': website
            }}
        )

        flash('Restaurante atualizado com sucesso!', 'success')
        return redirect(url_for('restaurantes'))

    return render_template('editar_restaurante.html', restaurante=restaurante)

if __name__ == '__main__':
    app.run(debug=True)
