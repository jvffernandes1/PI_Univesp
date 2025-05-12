from pymongo import MongoClient
from werkzeug.security import generate_password_hash
import random

# Conexão com o banco MongoDB (mesmo URI usado no Flask)
client = MongoClient("mongodb+srv://piunivesp:n6nOL31JSFoUDsnX@clusterpi.rxd1i.mongodb.net/restaurants_db?retryWrites=true&w=majority&appName=clusterPI")
db = client.restaurants_db

# Lista de nomes brasileiros
nomes = [
    "João Silva", "Maria Oliveira", "Carlos Souza", "Ana Paula", "Pedro Henrique",
    "Juliana Costa", "Lucas Almeida", "Fernanda Rocha", "Bruno Melo", "Camila Martins",
    "Rafael Lima", "Patrícia Gomes", "Gustavo Nunes", "Larissa Barbosa", "Felipe Teixeira",
    "Aline Ferreira", "Tiago Moreira", "Beatriz Ramos", "Daniel Cardoso", "Vanessa Monteiro"
]

# Geração e inserção de usuários
usuarios = []
for i, nome in enumerate(nomes):
    email = f"{nome.split()[0].lower()}.{nome.split()[1].lower()}{i}@gmail.com"
    senha_hash = generate_password_hash("senha123")
    usuario = {
        "name": nome,
        "email": email,
        "password": senha_hash,
        "is_admin": False  # Primeiro usuário é admin
    }
    usuarios.append(usuario)

# Inserção em massa no MongoDB
db.users.insert_many(usuarios)

print(f"{len(usuarios)} usuários inseridos com sucesso!")
