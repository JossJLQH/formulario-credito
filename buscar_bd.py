import sqlite3
import os

print(f"📁 Directorio de trabajo actual: {os.getcwd()}")

if os.path.exists('creditos.db'):
    print("✅ El archivo 'creditos.db' SÍ existe en esta carpeta.")
    conexion = sqlite3.connect('creditos.db')
    cursor = conexion.cursor()
    
    # Verificar qué tablas existen
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = cursor.fetchall()
    print(f"📋 Tablas encontradas: {tablas}")
    
    if ('solicitudes_credito',) in tablas:
        cursor.execute("SELECT COUNT(*) FROM solicitudes_credito")
        total = cursor.fetchone()[0]
        print(f"📊 Total de filas/registros en la tabla: {total}")
        
        cursor.execute("SELECT * FROM solicitudes_credito")
        filas = cursor.fetchall()
        for f in filas:
            print(f"  👉 Registro: {f}")
    conexion.close()
else:
    print("❌ El archivo 'creditos.db' NO existe en esta carpeta.")