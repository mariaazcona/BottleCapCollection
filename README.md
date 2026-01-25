# CapCollection

CapCollection es una aplicación ligera en **Streamlit** para gestionar, buscar y visualizar una colección personal de chapas de botella.  
Incluye un sistema de búsqueda por imagen basado en **embeddings generados con MobileNetV3 Small**, lo que permite encontrar chapas similares mediante inteligencia artificial.

---

## Características

- Importación desde Excel (`.xlsx`) con ID, marca, tipo e imagen.
- Búsqueda por marca.
- Búsqueda por imagen mediante embeddings (IA).
- Base de datos local en **SQLite**.
- Embeddings almacenados en **float16** para reducir espacio.
- Exportación de la colección a Excel.
- Funcionamiento completamente **offline**.
- Interfaz con tema claro/oscuro.
- Carga de embeddings en RAM para búsquedas rápidas.

---

## Estructura del proyecto

CapCollection/ 
│ 
├── app.py                        # Interfaz Streamlit 
├── modules/ 
│    ├── services.py              # Acceso a BD, búsquedas, embeddings en RAM 
│    ├── embeddings.py            # Modelo MobileNetV3 + generación de embeddings 
│    └── import_excel.py          # Importador desde Excel y generador de embeddings 
│
├── assets/ 
│    ├── styles.css               # Estilos personalizados 
│    ├── data/ 
│    │    ├── capcollection.db    # Base de datos SQLite 
│    │    ├── capcollection.xlsx  # Archivo maestro de la colección 
│    │    └── exports/            # Exportaciones generadas 
│    └── images/                  # Carpeta con imágenes de chapas
└── requirements.txt


---

## Requisitos

- Python 3.10+
- Dependencias:

streamlit
pillow
numpy
pandas
torch
torchvision


---

## Importación de datos

Antes de ejecutar la aplicación, importa los datos desde el Excel maestro:

python modules/import_excel.py


Esto generará la base de datos `capcollection.db` y calculará los embeddings de las imágenes.

---

## Ejecución

Para iniciar la aplicación:

streamlit run app.py


---

## Notas

- El sistema funciona completamente offline.
- Las imágenes deben estar en `assets/images/`.
- El archivo Excel debe estar en `assets/data/capcollection.xlsx`.
- Los embeddings se almacenan en la base de datos para acelerar las búsquedas.