from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import random

# Conexão com o banco
client = MongoClient("mongodb+srv://piunivesp:n6nOL31JSFoUDsnX@clusterpi.rxd1i.mongodb.net/restaurants_db?retryWrites=true&w=majority&appName=clusterPI")
db = client.restaurants_db

# Comentários simples
comentarios = [
    "Muito top!",
    "Legal, gostei bastante.",
    "Bom atendimento.",
    "Voltarei com certeza!",
    "Comida muito boa!",
    "Curti demais.",
    "Top demais.",
    "Amei!",
    "Excelente!",
    "Nota 10!"
]

# Buscar usuários e restaurantes
usuarios = list(db.users.find({}, {"_id": 1}))
restaurantes = list(db.restaurants.find({}, {"_id": 1}))

# Garantir que há dados suficientes
if not usuarios or not restaurantes:
    print("Sem usuários ou restaurantes suficientes para gerar avaliações.")
else:
    novas_avaliacoes = []
    for user in usuarios:
        num_avaliacoes = random.randint(2, 3)
        restaurantes_escolhidos = random.sample(restaurantes, min(num_avaliacoes, len(restaurantes)))

        for restaurante in restaurantes_escolhidos:
            user_id = user["_id"]
            restaurant_id = restaurante["_id"]

            # Verificar se o usuário já avaliou esse restaurante
            existe = db.ratings.find_one({
                "user_id": user_id,
                "restaurant_id": restaurant_id
            })

            if not existe:
                nova = {
                    "user_id": user_id,
                    "restaurant_id": restaurant_id,
                    "rating": random.randint(4, 5),
                    "comentario": random.choice(comentarios),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                novas_avaliacoes.append(nova)

    # Inserir avaliações novas
    if novas_avaliacoes:
        db.ratings.insert_many(novas_avaliacoes)
        print(f"{len(novas_avaliacoes)} avaliações inseridas com sucesso.")
    else:
        print("Nenhuma nova avaliação para inserir (todos já haviam avaliado).")
