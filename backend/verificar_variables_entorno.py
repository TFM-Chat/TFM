import os
from dotenv import load_dotenv

def verificar_variables_entorno(requeridas):
    """Verifica que todas las variables de entorno requeridas estén cargadas."""
    faltantes = []
    for var in requeridas:
        valor = os.getenv(var)
        if valor is None:
            faltantes.append(var)
        else:
            print(f"{var} = {valor}")

    if faltantes:
        print("\nAdvertencia: Las siguientes variables de entorno no están definidas en el archivo .env:")
        for var in faltantes:
            print(f"- {var}")
    else:
        print("\nTodas las variables de entorno requeridas están definidas.")

if __name__ == "__main__":
    # Cargar variables de entorno desde el archivo .env
    load_dotenv()

    # Lista de variables de entorno requeridas
    variables_requeridas = [
        "COSMOSDB_CONTAINER_VECTOR"
    ]

    verificar_variables_entorno(variables_requeridas)