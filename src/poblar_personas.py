from __future__ import annotations 

import os 
import random 
import re 
import time 
from decimal import Decimal

from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Table,
    MetaData,
    create_engine,
    func,
    insert,
    select,
    text,
)
from sqlalchemy.engine import URL


# Cargamos las variables del archivo .env 
# Esto evita escribir la contraseña de MySQL directamente en el codigo.
load_dotenv()


def obtener_variable(nombre: str, valor_por_defecto: str) -> str:
    """Obtiene una variable de entorno y usa un valor por defecto si no existe"""
    return os.getenv(nombre, valor_por_defecto).strip()


def obtener_booleano(nombre: str, valor_por_defecto: bool) -> bool:
    """Convierte variables de texto (true/false) a valores booleanos."""
    valor = os.getenv(nombre)

    if valor is None: 
        return valor_por_defecto
    
    return valor.strip().lower() in {"1", "true", "yes", "y", "si", "s"}


def validar_identificador_mysql(valor: str, nombre_variable: str) -> None:
    """
    Valida nombres de base de datos y tabla.
    Solo se permiten letras, numeros y guion bajo para evitar errores SQL.
    """
    if not re.fullmatch(r"[A-Za-z0-9_]+", valor):
        raise ValueError(
            f"{nombre_variable} solo puede contener letras, numeros y guion bajo. "
            f"Valor recibido: {valor}"
        )
    

def proteger_identificador(identificador: str) -> str: 
    """Protege nombres de base de datos o tablas en MySql."""
    return f"{identificador}"


#Configuracion tomada desde .env
DB_HOST = obtener_variable("DB_HOST", "localhost")
DB_PORT = int(obtener_variable("DB_PORT", "3306"))
DB_USER = obtener_variable("DB_USER", "root")
DB_PASSWORD = obtener_variable("DB_PASSWORD", "")
DB_NAME = obtener_variable("DB_NAME", "actividad_3_udea")
TABLE_NAME = obtener_variable("TABLE_NAME", "personas_luciano")

TOTAL_RECORDS = int(obtener_variable("TOTAL_RECORDS", "100000"))
BATCH_SIZE = int(obtener_variable("BATCH_SIZE", "5000"))
FAKER_LOCALE = obtener_variable("FAKER_LOCALE", "es_CO")
RESET_TABLE = obtener_booleano("RESET_TABLE", True)

validar_identificador_mysql(DB_NAME, "DB_NAME")
validar_identificador_mysql(TABLE_NAME, "TABLE_NAME")


def crear_url_conexion(nombre_bd: str | None = None) -> URL:
    """
    Construye la URL de conexion para SQLAlchemy usando PyMyDWL.
    
    El formato final equivale a: 
    mysql+pymysql://usuario:password@host:puerto/nombre_bd
    """
    return URL.create(
        "mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        database=nombre_bd,
        query={"charset": "utf8mb4"},
    )


def crear_base_de_datos_si_no_existe() -> None:
    """
    Crea la base de datos local si aún no existe. 
    El usuario de MySQL debe tener permisos para crear bases de datos.
    """
    engine_servidor = create_engine (
        crear_url_conexion(),
        pool_pre_ping=True,
        future=True,
    )

    with engine_servidor.begin() as conexion:
        conexion.execute (
            text(
                f"CREATE DATABASE IF NOT EXISTS {proteger_identificador(DB_NAME) } "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
    
    engine_servidor.dispose()


def definir_tabla_personas(metadata: MetaData) -> Table:
    """
    Define la estructura de la tabla personas_luciano.
    La tabla tiene: 
    - id como clave primaria (Primary Key - PK).
    - Mas de 7 atributos generados con Faker.
    """
    return Table(
        TABLE_NAME,
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("nombre", String(80), nullable=False),
        Column("apellido", String(80), nullable=False),
        Column("correo", String(150), nullable=False, unique=True),
        Column("telefono", String(40), nullable=False),
        Column("fecha_nacimiento", Date, nullable=False),
        Column("ciudad", String(100), nullable=False),
        Column("direccion", String(200), nullable=False),
        Column("empresa", String(120), nullable=False),
        Column("profesion", String(120), nullable=False),
        Column("fecha_registro", DateTime, nullable=False),
        Column("activo", Boolean, nullable=False),
        Column("saldo", Numeric(10,2), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )


def preparar_tabla(engine, metadata: MetaData, tabla_personas: Table) -> None:
    """
    Crea automaticamente la tabla si no existe.
    
    Para que la evidencia final muestre exactamente 100000 registros, 
    RESET_TABLE=true elimina y recrea la tabla antes de insertar.
    """
    if RESET_TABLE:
        metadata.drop_all(engine, tables=[tabla_personas])

    metadata.create_all(engine, tables=[tabla_personas])

def generar_persona(fake: Faker, numero: int) -> dict:
    """
    Genera una persona falsa con datos coherentes usando la funcion Faker.
    El numero se agrega al correo para garantizar que sea unico
    y evitar errores por duplicidad.
    """
    nombre = fake.first_name()
    apellido = fake.last_name()

    correo = f"{nombre}.{apellido}.{numero}@example.com".lower()
    correo = re.sub(r"[^a-z0-9.@_-]", "", correo)

    return {
        "nombre": nombre[:80],
        "apellido": apellido[:80],
        "correo": correo[:150],
        "telefono": fake.phone_number()[:40],
        "fecha_nacimiento": fake.date_of_birth(minimum_age=18, maximum_age=85),
        "ciudad": fake.city()[:100],
        "direccion": fake.address().replace("\n", ", ")[:200],
        "empresa": fake.company()[:120],
        "profesion": fake.job()[:120],
        "fecha_registro": fake.date_time_between(start_date="-5y", end_date="now"),
        "activo": random.choices([True, False], weights=[90, 10], k=1)[0],
        "saldo": Decimal(random.randint(0,300000000)) / Decimal("100"),
    }


def insertar_registros(engine, tabla_personas: Table) -> None:
    """
    Inserta 100000 registros usando insercion por lotes.

    Esta tecnica es mas eficiente que insertando uno por uno, porque envia
    grupos grandes de diccionarios a conn.execute().
    """
    Faker.seed(2026)
    random.seed(2026)

    fake = Faker(FAKER_LOCALE)
    total_insertado = 0
    inicio = time.perf_counter()

    with engine.begin() as conexion: 
        for inicio_lote in range(1, TOTAL_RECORDS + 1, BATCH_SIZE):
            fin_lote = min(inicio_lote + BATCH_SIZE - 1, TOTAL_RECORDS)

            lote = [
                generar_persona(fake, numero)
                for numero in range(inicio_lote, fin_lote + 1)
            ]

            conexion.execute(insert(tabla_personas), lote)

            total_insertado += len(lote)
            print(f"Insertados {total_insertado:,} de {TOTAL_RECORDS:,} registros...")

    duracion = time.perf_counter() - inicio 
    print(f"Insercion finalizada en {duracion:.2f} segundos.")


def contar_registros(engine,tabla_personas: Table) -> int: 
    """Ejecuta SELECT COUNT(*) para validar el total de registros insertados."""
    with engine.connect() as conexion: 
        total = conexion.execute (
            select(func.count()).select_from(tabla_personas)
        ).scalar_one()
        
    return total


def validad_calidad_datos(engine, table_name):
    """
    Valida nuevamente la calidad básica de los datos generados con Faker.
    Esta función no revisa solo la cantidad de registros, sino que verifica 
    que no existan campos vacíos y que los correos si sean únicos.
    """

    consultas = {
        "nombres_vacios": f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE nombre IS NULL OR nombre = ''
        """,
        "correos_vacios": f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE correo IS NULL OR correo = ''
        """,
        "ciudades_vacias": f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE ciudad IS NULL OR ciudad = ''
        """,
        "fechas_nacimiento_vacias": f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE fecha_nacimiento IS NULL
        """,
        "correos_duplicados": f"""
            SELECT COUNT(*)
            FROM (
                SELECT correo
                FROM {table_name}
                GROUP BY correo
                HAVING COUNT(*) > 1
            ) AS duplicados
        """
    }

    print("\nValidación de calidad de datos: ")

    with engine.connect() as conn: 
        errores = 0

        for nombre_validacion, consulta_sql in consultas.items():
            resultado = conn.execute(text(consulta_sql))
            total_problemas = resultado.scalar()

            print(f"{nombre_validacion}: {total_problemas}")

            if total_problemas > 0:
                errores += total_problemas
    
    if errores == 0:
        print("Validacion exitosa: los datos generados cumplen las reglas de calidad.")
    else: 
        raise ValueError(
            f"Se encontraron {errores} problemas de calidad en los datos generados."
        )


def main() -> None: 
    """
    Funcion principal del programa. 
    
    Flujo:
    1. Crea la base de datos si no existe.
    2. Conecta a MySQL con SQLAlchemy.
    3. Crea automaticamente la tabla personas_luciano
    4. Genera e inserta 100000 registros con Faker.
    5. Verifica el total con SELECT COUNT(*)
    """
    print("Iniciando Taller U3 - Automatizacion de BD con Python, Faker y Git")
    print(f"Base de datos: {DB_NAME}")
    print(f"Tabla: {TABLE_NAME}")
    print(f"Registros a insertar: {TOTAL_RECORDS:,}")

    crear_base_de_datos_si_no_existe()

    engine = create_engine(
        crear_url_conexion(DB_NAME),
        pool_pre_ping=True,
        future=True,
    )

    metadata = MetaData()
    tabla_personas = definir_tabla_personas(metadata)

    try:
        preparar_tabla(engine, metadata, tabla_personas)
        insertar_registros(engine, tabla_personas)

        total = contar_registros(engine, tabla_personas)
        print(f"Resultado de SELECT COUNT(*): {total:,}")

        if total != TOTAL_RECORDS:
            raise RuntimeError(
                f"Error de validacion: se esperaban {TOTAL_RECORDS:,} registros, "
                f"pero se encontraron {total:,}."
            )
        
        print("Proceso completado correctamente.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()