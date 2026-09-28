import sqlite3

def consultar_solicitudes():
    # 1. Conectar a la base de datos
    conexion = sqlite3.connect('creditos.db')
    cursor = conexion.cursor()

    # 2. Consultar todas las filas de la tabla solicitudes_credito
    cursor.execute('''
        SELECT id, nombre, apellidos, curp, telefono, email, monto_solicitado, estatus, fecha_registro 
        FROM solicitudes_credito
    ''')
    
    registros = cursor.fetchall()
    conexion.close()

    # 3. Mostrar los resultados en la terminal
    print("\n=======================================================")
    print("       SOLICITUDES DE CRÉDITO REGISTRADAS")
    print("=======================================================\n")

    if not registros:
        print("No hay solicitudes guardadas por el momento.\n")
        return

    for reg in registros:
        print(f"📌 ID Solicitud: {reg[0]}")
        print(f"   Cliente:      {reg[1]} {reg[2]}")
        print(f"   CURP:         {reg[3]}")
        print(f"   Teléfono:     {reg[4]}")
        print(f"   Email:        {reg[5]}")
        print(f"   Monto:        ${reg[6]:,}")
        print(f"   Estatus:      {reg[7]}")
        print(f"   Fecha/Hora:   {reg[8]}")
        print("-" * 55)

if __name__ == '__main__':
    consultar_solicitudes()