import secrets


def generar_api_key() -> str:
    """
    Genera una API Key segura y url-safe (43 caracteres aprox).
    Ideal para usar en headers HTTP (X-API-Key).
    """
    return secrets.token_urlsafe(32)


def main() -> None:
    print(" Generador de API Key Segura (sin dependencias externas)")
    print("-" * 50)

    api_key = generar_api_key()

    print("\n Tu nueva API Key generada es:\n")
    print(f"{api_key}")
    print("\n" + "-" * 50)
    print("Instrucciones:")
    print("1. Copia la clave de arriba.")
    print("2. Pégala en tu archivo .env en la variable RAG_API_KEY=")
    print("3. (Opcional) Usa esta misma clave para configurar tu servidor FastAPI.")


if __name__ == "__main__":
    main()
