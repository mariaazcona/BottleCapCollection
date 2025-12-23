# 🍾 CapCollection  
### AI-Powered Bottle Cap Catalog Manager

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)

CapCollection is a lightweight offline desktop application designed to organize, browse, and search your personal bottle cap collection.  
It uses deep-learning image embeddings to match caps visually and provides a fast, clean, and intuitive interface.

---

## ✨ Features

- 📥 **Excel Import**
  - Load caps from an `.xlsx` file with ID, brand, type, and image path.

- 🧠 **AI Image Similarity Search**
  - Compare a new image to your database using MobileNetV3-Small embeddings.

- ⚡ **Optimized Performance**
  - Model loads only when needed  
  - Embeddings saved as float16 (half memory usage)  
  - Instant vectorized similarity search

- 🗂️ **SQLite Local Database**
  - Fully offline  
  - Fast, compact, persistent

- 🖥️ **Tkinter Desktop Interface**
  - Search by brand  
  - Search by image  
  - Preview cap image + metadata  
  - Export updated Excel files

- 💾 **Automatic Exports**
  - Timestamped Excel backups inside `exports/`

---

## 📁 Project Structure
CapCollection/
│
├── chapas_gui.py # Main GUI application
├── funciones.py # Database and logic
├── funciones_modelo.py # AI model + image embeddings
├── importar_excel.py # Excel importer → fills SQLite + embeddings
│
├── chapas.db # (Auto-generated) database
├── imagenes/ # User's image folder
└── exports/ # Auto-generated exports folder

---

## 🧰 Requirements

- Python **3.10+**
- pip packages:

```bash
pip install pillow numpy pandas openpyxl torch torchvision


