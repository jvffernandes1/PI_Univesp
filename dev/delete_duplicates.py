from pymongo import MongoClient

# Conexão com o banco MongoDB
client = MongoClient("mongodb+srv://piunivesp:n6nOL31JSFoUDsnX@clusterpi.rxd1i.mongodb.net/restaurants_db?retryWrites=true&w=majority&appName=clusterPI")
db = client.restaurants_db

# Cria um índice dos e-mails que já viu
emails_vistos = set()
usuarios = list(db.users.find({}))  # Carrega todos os usuários

removidos = 0
for user in usuarios:
    email = user.get("email")
    if email in emails_vistos:
        db.users.delete_one({"_id": user["_id"]})
        removidos += 1
    else:
        emails_vistos.add(email)

print(f"{removidos} usuários duplicados removidos com base no e-mail.")
