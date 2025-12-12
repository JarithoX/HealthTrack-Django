# HealthTrack - Proyecto Final

Interfaz de usuario web construida con **Django**. Maneja las vistas, sesiones de usuario y consume la API de Node.js para todas las operaciones de datos.

## 🛠️ Tecnologías
* **Framework:** Django (Python )
* **Estilos:** Bootstrap 
* **Servidor Prod:** Gunicorn + WhiteNoise (para estáticos)
* **Despliegue:** Google Cloud Run (Dockerizado)

---

REPOSITORIO:
```powershell
https://github.com/JarithoX/HealthTrack-Django.git
```

Crear un entorno virtual:

1- Instala virtualenv si aún no lo tienes.

```powershell
 pip install virtualenv
```

2-Crea el entorno Virtual.

```powershell
Python -m venv entorno 
```
 
3- Entra a la carpeta y activa el entorno.

```powershell
.\Activate.ps1
```

4- Instalar DJANGO

```powershell
pip install django
```

```powershell
pip install requests
```

## Ejecutar proyecto:


1.1.- Activa el entorno virtual en una sola linea
```powershell
cd .\entorno\Scripts\ ; .\Activate.ps1 ; cd.. ; cd..
```

2.- Volver a la carpeta raiz [cd..] y correr el servidor:
```powershell
python manage.py runserver
```

2.1.- Migrar la base de datos:
```powershell
.\entorno\Scripts\python.exe manage.py migrate
```

3. instalar dependencias:
```powershell
pip install -r requirements.txt
```

---

## 💻 Desarrollo Local (Cómo ejecutar en tu PC)

### 1. Prerrequisitos
* Python 3.10+ instalado.
* Entorno virtual creado (`python -m venv entorno`).

### 2. Configuración de Variables (`.env`)
En local, Django puede usar un archivo `.env` o valores por defecto en `settings.py`.
Asegúrate de que la URL de la API apunte a tu local:
```env
DEBUG=True
API_URL=http://localhost:3000/api
SECRET_KEY=django-insecure-...
```

### 3. Despliegue en Google Cloud Run
```powershell
gcloud run deploy healthtrack-django --source . --region us-central1 --allow-unauthenticated
```