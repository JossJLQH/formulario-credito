import sqlite3

def borrar_registro_por_curp(curp_a_borrar):
    conexion = sqlite3.connect('creditos.db')
    cursor = conexion.cursor()
    
    # Eliminamos la fila correspondiente a la CURP
    cursor.execute("DELETE FROM solicitudes_credito WHERE curp = ?", (curp_a_borrar,))
    
    filas_borradas = cursor.rowcount
    conexion.commit()
    conexion.close()
    
    if filas_borradas > 0:
        print(f"✅ Se eliminó con éxito el registro con CURP: {curp_a_borrar}")
    else:
        print(f"⚠️ No se encontró ningún registro con la CURP: {curp_a_borrar}")

if __name__ == '__main__':
    # Escribe aquí la CURP que quieres borrar para volver a probar
    curp_prueba = input("Escribe la CURP que deseas eliminar de la BD: ").strip()
    if curp_prueba:
        borrar_registro_por_curp(curp_prueba)