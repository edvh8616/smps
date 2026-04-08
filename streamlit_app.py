import streamlit as st
import requests
import json
from datetime import datetime
from typing import Optional

st.set_page_config(
    page_title="Sistema de Alertas Telegram",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 Sistema de Alertas Telegram")
st.markdown("Envía alertas a Telegram a través de n8n")

# Sidebar para configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    n8n_url = st.text_input(
        "URL de n8n",
        value="https://impoundable-nikolai-unalphabetical.ngrok-free.dev",
        help="URL base de tu instancia de n8n"
    )
    
    webhook_path = st.text_input(
        "Ruta del webhook",
        value="telegram-alert",
        help="Ruta del webhook sin el '/' inicial"
    )
    
    api_endpoint = f"{n8n_url}/webhook/{webhook_path}"
    
    st.info(f"📍 Endpoint: `{api_endpoint}`")
    
    st.divider()
    st.subheader("📋 Instrucciones")
    st.markdown("""
    1. **Obtén tu Bot Token de Telegram:**
       - Habla con [@BotFather](https://t.me/botfather) en Telegram
       - Crea un nuevo bot
       - Copia el token
    
    2. **Obtén tu Chat ID:**
       - Envía un mensaje a tu bot
       - Ve a `https://api.telegram.org/bot<TOKEN>/getUpdates`
       - Copia el `chat.id`
    
    3. **Configura las variables en n8n:**
       - Ve a Settings → Variables
       - Crea `TELEGRAM_BOT_TOKEN`
       - Crea `TELEGRAM_CHAT_ID`
    """)

st.divider()

# Formulario de alertas
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Nueva Alerta")
    
    title = st.text_input(
        "Título de la alerta",
        placeholder="Ej: Error en Base de Datos",
        key="alert_title"
    )
    
    severity = st.selectbox(
        "Nivel de severidad",
        options=["info", "warning", "error", "critical"],
        format_func=lambda x: {
            "info": "ℹ️ Información",
            "warning": "⚠️ Advertencia",
            "error": "❌ Error",
            "critical": "🔴 Crítico"
        }.get(x, x),
        key="severity"
    )
    
    message = st.text_area(
        "Mensaje detallado",
        placeholder="Describe los detalles de la alerta...",
        height=150,
        key="alert_message"
    )

with col2:
    st.subheader("📤 Envío")
    
    # Mostrar resumen
    st.markdown("**Resumen de la alerta:**")
    
    preview_data = {
        "title": title or "Sin título",
        "severity": severity,
        "message": message or "Sin mensaje",
        "timestamp": datetime.now().isoformat()
    }
    
    st.json(preview_data, expanded=False)
    
    # Botón de envío
    if st.button("📨 Enviar Alerta", use_container_width=True, type="primary"):
        if not title.strip():
            st.error("❌ Por favor, ingresa un título para la alerta")
        elif not message.strip():
            st.error("❌ Por favor, ingresa un mensaje para la alerta")
        else:
            with st.spinner("Enviando alerta..."):
                try:
                    response = requests.post(
                        api_endpoint,
                        json={
                            "title": title,
                            "message": message,
                            "severity": severity
                        },
                        timeout=10
                    )
                    
                    if response.status_code in [200, 201]:
                        result = response.json()
                        st.success("✅ ¡Alerta enviada exitosamente!")
                        st.json(result)
                        
                        # Guardar en historial
                        st.session_state.last_alert = preview_data
                        st.session_state.last_alert["sent_at"] = datetime.now()
                        st.session_state.last_alert["status"] = "enviado"
                        
                    else:
                        st.error(f"❌ Error {response.status_code}: {response.text}")
                        
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ No se puede conectar a {api_endpoint}")
                    st.info("Asegúrate de que n8n esté ejecutándose en esa dirección")
                    
                except requests.exceptions.Timeout:
                    st.error("❌ Timeout: La solicitud tardó demasiado")
                    
                except Exception as e:
                    st.error(f"❌ Error inesperado: {str(e)}")

st.divider()

# Historial de alertas
st.subheader("📜 Historial de Alertas")

if "alerts_history" not in st.session_state:
    st.session_state.alerts_history = []

if "last_alert" in st.session_state:
    st.session_state.alerts_history.insert(0, st.session_state.last_alert)
    st.session_state.last_alert = None

if st.session_state.alerts_history:
    for idx, alert in enumerate(st.session_state.alerts_history[:10]):
        with st.container(border=True):
            cols = st.columns([2, 1, 2])
            
            with cols[0]:
                severity_emoji = {
                    "info": "ℹ️",
                    "warning": "⚠️",
                    "error": "❌",
                    "critical": "🔴"
                }.get(alert.get("severity", "info"), "•")
                
                st.markdown(f"**{severity_emoji} {alert.get('title', 'Sin título')}**")
                st.caption(alert.get("message", "Sin mensaje")[:100] + "...")
            
            with cols[1]:
                status_color = {
                    "enviado": "green",
                    "pendiente": "orange"
                }.get(alert.get("status", "pendiente"), "gray")
                st.markdown(f":{status_color}[{alert.get('status', 'pendiente').upper()}]")
            
            with cols[2]:
                if "sent_at" in alert:
                    time_str = alert["sent_at"].strftime("%H:%M:%S")
                else:
                    time_str = alert.get("timestamp", "N/A")[:19]
                st.caption(f"🕐 {time_str}")
else:
    st.info("No hay alertas en el historial aún")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    <p>🔗 Sistema de alertas integrado con n8n y Telegram</p>
    <p>Desarrollado con Streamlit</p>
</div>
""", unsafe_allow_html=True)
