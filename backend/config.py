class Config:
    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://admin:xxxxxxxxxx@ms.mysql.database.azure.com:3306/chat'
    SQLALCHEMY_TRACK_MODIFICATIONS = False