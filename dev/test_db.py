from pymongo import MongoClient

uri = "mongodb+srv://piunivesp:n6nOL31JSFoUDsnX@clusterpi.rxd1i.mongodb.net/restaurants_db?retryWrites=true&w=majority&appName=clusterPI"
client = MongoClient(uri)

try:
    client.admin.command('ping')  # Testa a conexão com o servidor
    print("✅ Conectado ao MongoDB com sucesso!")
except Exception as e:
    print(f"❌ Erro ao conectar ao MongoDB: {e}")
