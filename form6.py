import streamlit as st
import pandas as pd
import datetime
import sqlite3

st.set_page_config(page_title='FORMULARIO', page_icon='📋')
st.title('Tutorial de formularios y BBDD')

# crear la BBDD y la tabla si no existen
def inicializar_db():
    conexion = sqlite3.connect('users.db')
    cursor = conexion.cursor()
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS CLIENTES(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   nombre TEXT,
                   password TEXT,
                   fecha_registro TEXT
                   )   
                '''
                   )
    conexion.commit()
    conexion.close()


def inicializar_historial():
    conexion = sqlite3.connect('users.db')
    cursor = conexion.cursor()
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS HISTORIAL(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   usuario TEXT,
                   accion TEXT,
                   fecha_hora TEXT
                   )   
                '''
                   )
    conexion.commit()
    conexion.close()

# es para insertar un nuevo registro de cliente
def registrar_cliente(nombre, password):
    conexion = sqlite3.connect('users.db')
    cursor = conexion.cursor()
    fecha = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    # verificar si ya existe el cliente con ese nombre y contraseña
    cursor.execute("SELECT id FROM CLIENTES WHERE nombre = ? AND password = ?", (nombre, password))
    if cursor.fetchone():
        conexion.close()
        return False # significa que ya existe el cliente
    
    # inserta nuevo cliente
    cursor.execute("INSERT INTO CLIENTES (nombre, password, fecha_registro) VALUES (?, ?, ?)", (nombre, password, fecha))
    conexion.commit()
    conexion.close()
    return True


def verificar_cliente(nombre, password):
    conexion = sqlite3.connect('users.db')
    cursor = conexion.cursor()
    # como solo vamos a reemplazar un valor que es el nombre, entonces se pone la coma al final, si fueran mas valores como (nombre, password, etc) no lleva la coma al final
    cursor.execute("SELECT id, password FROM CLIENTES WHERE nombre = ?", (nombre,))
    resultado = cursor.fetchone()
    conexion.close()
    if resultado:
        return resultado[1] == password # ¿la contraseña que esta guardada es igual a la que escribio el usuario?
    else:
        return None


def registrar_accion(usuario, accion):
    conexion = sqlite3.connect('users.db')
    cursor = conexion.cursor()
    fecha = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    cursor.execute("INSERT INTO HISTORIAL (usuario, accion, fecha_hora) VALUES (?, ?, ?)", (usuario, accion, fecha))
    conexion.commit()
    conexion.close()

# Inicializar la base de datos
inicializar_db()
inicializar_historial()

#menu lateral
menu = ['Inicio', 'Formulario de Ingreso - Registro', 'BBDD', 'Historial']
seleccion = st.sidebar.selectbox('Selecciona un tema', menu)

if seleccion == 'Inicio':
    st.header('BIENVENIDO')
    st.write(
        '''
        Aqui encontraras:
        - Inicio de sesion para ingresar a una BBDD
        - Registro de usuario y contraseña
        - Visualizacion y descarga de la BBDD
        '''
    )

elif seleccion == 'Formulario de Ingreso - Registro':
    st.title('Inicio de sesión')

    if "mostrar_registro" not in st.session_state:
        st.session_state.mostrar_registro = False
    
    # login
    if not st.session_state.mostrar_registro:
        with st.form(key='login_form'):
            usuario_login = st.text_input('Nombre de usuario')
            contrasena_login = st.text_input('Contraseña', type='password')
            enviar_login = st.form_submit_button(label='Iniciar sesion')
        
        if enviar_login:
            if usuario_login.strip() == '' or contrasena_login.strip() == '':
                st.warning('Por favor completa todos los campos')
                registrar_accion(usuario_login, "Intento de sesion con campos vacios")
            else:
                validacion = verificar_cliente(usuario_login, contrasena_login)
                if validacion is None:
                    st.error('Usuario no registrado')
                    registrar_accion(usuario_login, "Intento de sesion con usuario no registrado")
                elif validacion:
                    st.success(f'Bienvenid@ {usuario_login}!')
                    registrar_accion(usuario_login, "Sesion iniciada con exito")
                else:
                    st.error('Usuario o contraseña incorrecta')
                    registrar_accion(usuario_login, "Intento de sesion con usuario o contraseña incorrecta")
        if st.button('¿No tienes cuenta? Registrate'):
            st.session_state.mostrar_registro = True
            st.rerun()
    
    # registro
    else:
        st.subheader('Formulario de registro')
        with st.form(key='registro_form'):
            nuevo_usuario= st.text_input('Elige un nombre de usuario')
            nueva_contrasena = st.text_input('Elige una contraseña', type='password')
            enviar_registro = st.form_submit_button(label='Registrarse')
        
        if enviar_registro:
            if nuevo_usuario.strip() == '' or nueva_contrasena.strip() == '':
                st.warning('Por favor completa todos los campos')
            elif registrar_cliente(nuevo_usuario, nueva_contrasena):
                st.success(f'Usuario {nuevo_usuario} creado con exito')
                st.session_state.mostrar_registro = False
            else:
                st.error('El usuario ya existe en la BBDD')
        
        if st.button('¿Ya tienes cuenta? Inicia sesion'):
            st.session_state.mostrar_registro = False

elif seleccion == 'BBDD':
    st.markdown('---')
    st.header('🔐 Acceso a base de datos')

    # contraseña para ver la base de datos
    clave_correcta = "admin123"

    constrasena_visualizar = st.text_input('Ingresa la contraseña para ver la base de datos', type='password')
    archivo_db = st.file_uploader('Sube el archivo .db de sqlite3', type=['db'])

    if archivo_db and constrasena_visualizar:
        if constrasena_visualizar == clave_correcta:
            # guardar el archivo subido
            ruta_temporal = 'subida_temp.db'
            with open(ruta_temporal, 'wb') as f:
                f.write(archivo_db.read())
            
            # conectarse y mostrar las tablas
            conn = sqlite3.connect(ruta_temporal)
            cursor = conn.cursor()

            # obtener las tablas
            cursor.execute('SELECT name FROM sqlite_master WHERE type = "table"')
            tablas = cursor.fetchall()

            if tablas:
                st.success('✔️ Acceso concedido. Mostrando tablas:')
                for nombre_tabla in tablas:
                    nombre = nombre_tabla[0] # me dice que me muestre la primer tabla guardada en sql
                    st.subheader(f'📋 Tabla: {nombre}')
                    df = pd.read_sql(f'SELECT * FROM {nombre}', conn)
                    st.dataframe(df)
            else:
                st.info('La base de datos no contiene tablas')
            conn.close()
        else:
            st.error('❌ Contraseña incorrecta. Acceso denegado')

elif seleccion == 'Historial':
    st.header('🕙 Acciones que han realizado los usuarios')

    conexion = sqlite3.connect('users.db')
    df_historial = pd.read_sql_query("SELECT * FROM HISTORIAL ORDER BY fecha_hora DESC", conexion) # ordena todos los registros segun la fecha y hora en orden descendente
    conexion.close()

    if not df_historial.empty:
        st.dataframe(df_historial)
    else:
        st.info('No hay acciones registradas aún')