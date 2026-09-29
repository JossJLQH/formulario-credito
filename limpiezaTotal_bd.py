import sqlite3

conexion = sqlite3.connect('creditos.db')
cursor = conexion.cursor()

# Borra todas las filas de la tabla
cursor.execute("DELETE FROM solicitudes_credito;")

conexion.commit()
conexion.close()
print("🧹 ¡Se han eliminado TODOS los registros de prueba!")