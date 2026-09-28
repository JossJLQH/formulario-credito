CREATE TABLE solicitudes_credito (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    fecha_nacimiento TEXT NOT NULL,
    curp TEXT UNIQUE NOT NULL,
    telefono TEXT NOT NULL,
    email TEXT NOT NULL,
    monto_solicitado INTEGER NOT NULL,
    ocupacion TEXT NOT NULL,
    ingreso_mensual INTEGER NOT NULL,
    estatus TEXT DEFAULT 'PENDIENTE',
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
);