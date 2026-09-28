import sqlite3

# Conectar/crear el archivo de base de datos
conexion = sqlite3.connect('creditos.db')

# Leer las instrucciones de tu archivo schema.sql
with open('base_de_datos.sql', 'r', encoding='utf-8') as f:
    script_sql = f.read()

# Ejecutar las instrucciones para crear la tabla
conexion.executescript(script_sql)

print("¡Base de datos 'creditos.db' y tabla creadas exitosamente!")
conexion.close()