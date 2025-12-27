# CapCollection

CapCollection es una aplicación ligera en Streamlit para gestionar, buscar y visualizar una colección personal de chapas de botella.  
Utiliza embeddings generados con MobileNetV3 para realizar búsquedas por similitud de imagen.

---

## Características

- Importación desde Excel (`.xlsx`) con ID, marca, tipo e imagen.
- Búsqueda por marca.
- Búsqueda por imagen mediante embeddings.
- Base de datos local en SQLite.
- Embeddings almacenados en formato float16 para reducir espacio.
- Exportación de la colección a Excel.
- Funcionamiento completamente offline.

---

## Estructura del proyecto

CapCollection/
│
├── app.py                      # Interfaz Streamlit
├── modules/
│   ├── services.py             # Acceso a BD, búsquedas, embeddings en RAM
│   ├── funciones_modelo.py    # Modelo MobileNetV3 + generación de embeddings
│   └── import_excel.py        # Importador desde Excel
│
├── data/
│   ├── capcollection.db        # Base de datos SQLite
│   └── capcollection.xlsx      # Archivo maestro de importación
│
├── images/                    # Carpeta con imágenes de chapas
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

## Ejecución
streamlit run app.py