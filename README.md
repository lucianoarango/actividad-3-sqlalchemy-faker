# Taller U3 - Automatización de BD con Python, Faker y Git
## Por: Luciano Arango Zapata

Se busca con este proyecto automatizar la creación y poblado de una base de datos MySQL local usando Python, SQLAlchemy y Faker.

El script en Python crea automaticamente una tabla con el formato `personas_luciano` e inserta 100000 registros falsos pero coherentes, gracias a la función Faker, para un contexto de ciencia de datos.

## Tecnologías usadas

- Python 3.10+
- MySQL
- SQLAlchemy
- PyMySQL
- Faker
- python-dotenv
- Git y GitHub
- DBeaver

## Estructura del proyecto

```text
actividad-3-sqlalchemy-faker/
    src/
        poblar_personas.py
    evidencias/
        select_count.sql
        select_count_dbeaver.png
    .env.example
    .gitignore
    README.md
    requirements.txt
```

## Configuración

Crear entorno virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
Copy-Item .env.example .env
```

Editar `.env` con las credenciales reales de MySQL.

## Ejecución

```powershell
python src/poblar_personas.py
```

## ¿Qué hace el script?

1. Lee las variables de conexión desde `.env`.
2. Crea la base de datos `actividad_3_udea` si no existe.
3. Crea automaticamente la tabla `personas_luciano`.
4. Genera datos falsos con Faker.
5. Inserta 100000 registros usando inserción por lotes (buena práctica)
6. Valida el resultado con `SELECT COUNT(*)`.

## Consulta de validación en DBeaver

```sql 
USE actividad_3_udea;

SELECT COUNT(*) AS total_registros
FROM personas_tunombre;
```

Resultado esperado: 
```text
100000
```

## Seguridad

El archivo `.env` contiene credenciales reales y está ignorado por Git.
El archivo `.env.example` se incluye como plantilla publica sin contraseñas reales.


## Calidad de datos 

Para el quinto commit se hace una funcion que rectifica que además de existir los 100000
registros en la tabla personas_luciano, verifica que sean correctos, es decir, sin campos
vacíos y sin repetidos en columnas especificadas.