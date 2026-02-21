import keep_alive
keep_alive.keep_alive()
import telebot
from google import genai
from PIL import Image
import os
from dotenv import load_dotenv
## Carga de variables de .env
load_dotenv()
api_key = os.getenv("API_KEY_GEMINI_ID")
token_telegram = os.getenv("TOKEN_TELEGRAM")


cliente_gemini = genai.Client(api_key=api_key)
bot = telebot.TeleBot(token_telegram)
conversaciones = {}

print("🤖 Iniciando Súper Bot Definitivo (Ahora lee documentos)...")

# ==========================================
# 2. EL BOT TE ENVÍA UNA FOTO (/foto)
# ==========================================
@bot.message_handler(commands=['foto'])
def enviar_foto(mensaje):
    bot.reply_to(mensaje, "Buscando una foto genial...")
    url_imagen = "https://www.bing.com/images/search?view=detailV2&ccid=exwQ8cEG&id=A21991CBC3817719EB76E5BC82944597C6840C83&thid=OIP.exwQ8cEG8zKeF_GwlZD6AAHaFj&mediaurl=https%3a%2f%2fth.bing.com%2fth%2fid%2fR.7b1c10f1c106f3329e17f1b09590fa00%3frik%3dgwyExpdFlIK85Q%26riu%3dhttp%253a%252f%252f2.bp.blogspot.com%252f-C0a-vDg8cfs%252fT6NjNmTxdkI%252fAAAAAAAABGQ%252fvXXueiiMLEo%252fs1600%252fAfrican%252bGorilla%252bAfrica%252bGorila%252bbeautiful%252bdangerous%252bBaby%252bsitting---Western-Lowland-Gorilla%252bdangerous%252banimal%252battacks%252bof%252bUganda%252bKenya%252bTanzania%252bSouth%252bAfrica%252banimal%252bpictures.jpg%26ehk%3doIpiRotcP0OOGZDb0CFwK3d7xpWOFKu2iedHWlAfWjE%253d%26risl%3d%26pid%3dImgRaw%26r%3d0&exph=1200&expw=1600&q=gorila&FORM=IRPRST&ck=F75D392E3FF29F7D0ED92CFF33404257&selectedIndex=11&itb=0"
    bot.send_photo(mensaje.chat.id, url_imagen, caption="¡Mira, un gorila!")

# ==========================================
# 3. EL BOT LEE TUS IMÁGENES
# ==========================================
@bot.message_handler(content_types=['photo'])
def leer_imagen(mensaje):
    id_usuario = mensaje.chat.id
    bot.reply_to(mensaje, "👀 Analizando tu imagen...")
    bot.send_chat_action(id_usuario, 'typing')

    try:
        file_info = bot.get_file(mensaje.photo[-1].file_id)
        foto_descargada = bot.download_file(file_info.file_path)
        ruta_foto = "foto_temporal.jpg"
        
        with open(ruta_foto, 'wb') as archivo_nuevo:
            archivo_nuevo.write(foto_descargada)

        imagen_para_gemini = Image.open(ruta_foto)
        
        respuesta_ia = cliente_gemini.models.generate_content(
            model='gemini-2.5-flash',
            contents=[imagen_para_gemini, "Describe con mucho detalle todo lo que ves en esta imagen."]
        )
        
        # Dividimos el texto si es muy largo
        texto_completo = respuesta_ia.text
        for i in range(0, len(texto_completo), 4000):
            bot.reply_to(mensaje, texto_completo[i:i+4000])
            
        os.remove(ruta_foto)

    except Exception as e:
        bot.reply_to(mensaje, "Hubo un problema leyendo la imagen.")
        print(f"Error: {e}")

# ==========================================
# 4. ¡NUEVO! EL BOT LEE DOCUMENTOS (PDF, TXT, DOCX)
# ==========================================
@bot.message_handler(content_types=['document'])
def leer_documento(mensaje):
    id_usuario = mensaje.chat.id
    bot.reply_to(mensaje, "📚 Recibí tu documento. Lo estoy leyendo, dame unos segundos...")
    bot.send_chat_action(id_usuario, 'typing')

    try:
        # A. Descargamos el archivo de Telegram a tu computadora
        file_info = bot.get_file(mensaje.document.file_id)
        archivo_descargado = bot.download_file(file_info.file_path)
        nombre_archivo = mensaje.document.file_name
        
        with open(nombre_archivo, 'wb') as nuevo_archivo:
            nuevo_archivo.write(archivo_descargado)

        # B. Subimos el archivo a los servidores de Gemini
        print(f"Subiendo {nombre_archivo} a Gemini...")
        archivo_gemini = cliente_gemini.files.upload(file=nombre_archivo)

        # C. Le pedimos a Gemini que lo lea y haga un resumen
        instruccion = "Eres un analista experto. Lee este documento y hazme un resumen detallado con los puntos más importantes."
        respuesta_ia = cliente_gemini.models.generate_content(
            model='gemini-2.5-flash',
            contents=[archivo_gemini, instruccion]
        )
        
        # D. Enviamos la respuesta a Telegram (cortada por si es muy larga)
        texto_completo = respuesta_ia.text
        for i in range(0, len(texto_completo), 4000):
            bot.reply_to(mensaje, texto_completo[i:i+4000])

        # E. Limpieza: Borramos el archivo de tu PC y de la nube de Google
        os.remove(nombre_archivo)
        cliente_gemini.files.delete(name=archivo_gemini.name)
        print("Limpieza completada.")

    except Exception as e:
        bot.reply_to(mensaje, "No pude leer este documento. Asegúrate de que sea un PDF o archivo de texto válido.")
        print(f"Error con el documento: {e}")

# ==========================================
# 5. LÓGICA DE TEXTO NORMAL
# ==========================================
@bot.message_handler(func=lambda msg: True)
def responder_a_usuario(mensaje):
    id_usuario = mensaje.chat.id
    texto_usuario = mensaje.text
    bot.send_chat_action(id_usuario, 'typing')
    
    if id_usuario not in conversaciones:
        conversaciones[id_usuario] = cliente_gemini.chats.create(model="gemini-2.5-flash")
    
    try:
        respuesta_ia = conversaciones[id_usuario].send_message(texto_usuario)
        
        # También le ponemos el seguro contra mensajes largos aquí
        texto_completo = respuesta_ia.text
        for i in range(0, len(texto_completo), 4000):
            bot.reply_to(mensaje, texto_completo[i:i+4000])
            
    except Exception as e:
        bot.reply_to(mensaje, "Tuve un corto circuito.")
        print(f"Error de texto: {e}")

# ==========================================
print("✅ Bot Definitivo en línea. ¡Ve a probarlo!")
bot.infinity_polling()