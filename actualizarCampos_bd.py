import sqlite3

def agregar_columna_estatus():
    conexion = sqlite3.connect('creditos.db')
    cursor = conexion.cursor()
    
    try:
        # Agregamos la columna estatus con valor por defecto 'Pendiente'
        cursor.execute("ALTER TABLE solicitudes_credito ADD COLUMN estatus TEXT DEFAULT 'Pendiente';")
        conexion.commit()
        print("✅ Columna 'estatus' agregada con éxito a la base de datos.")
    except sqlite3.OperationalError:
        print("ℹ️ La columna 'estatus' ya existía en la tabla.")
    finally:
        conexion.close()

if __name__ == '__main__':
    agregar_columna_estatus()