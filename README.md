# Acne Type Classification System Using Hybrid Transfer Learning and Synthetic GAN-Based Augmentation

A state-of-the-art Deep Learning project and web application designed to improve acne type classification accuracy. This project integrates a robust **Django web backend** with powerful **hybrid transfer learning models (ResNet50 & VGG16)** and **synthetic GAN-based augmentation (DCGAN)** to accurately detect and classify various acne types (e.g., Pustules, Whiteheads, Blackheads, Papules, Nodules) and reject out-of-distribution (OOD) non-face inputs.

---

## 🌟 Key Features

### 🧠 Deep Learning & AI Core
- **Hybrid Transfer Learning**: Utilizes pre-trained ResNet50 and VGG16 models optimized for specific dermatological feature extraction.
- **GAN-Based Data Augmentation**: Employs Deep Convolutional GANs (DCGAN) to generate high-fidelity synthetic samples, resolving class imbalance and boosting classification accuracy.
- **Out-of-Distribution (OOD) Rejection**: Integrates a ResNet50-based feature extractor and hybrid rejection model to automatically detect and discard non-face or non-acne images.
- **Acne Detection & Localization**: Integrates YOLO-based models (`acne_yolo.pt`) to precisely localize facial acne regions.

### 💻 Modern Web Application (Django)
- **Cinematic Dark Theme UI**: A gorgeous, premium, glassmorphism-inspired UI optimized for medical/technical systems.
- **User Dashboard & Authentication**: Fully featured registration, secure login, forgot password flow with dynamic email OTP verification, and profile management.
- **Multi-Mode Classification**:
  - **Upload Scan**: Analyze static skin images with real-time feedback, confidence scores, and visual annotations.
  - **Live Camera Scan**: Real-time webcam integration for live face scanning and on-the-fly analysis.
- **Historical Analysis**: Track user prediction history over time with dynamic prediction cards.
- **Robust Admin Portal**: Dedicated admin panel to manage users, view registrations, and oversee classification metrics.

---

## 🛠️ Tech Stack

- **Backend Framework**: Django (Python)
- **Database**: SQLite / MySQL (configurable)
- **Deep Learning**: TensorFlow, Keras, PyTorch, OpenCV, Scikit-learn
- **Frontend**: HTML5, Modern CSS3 (Glassmorphism, custom dark mode stylesheets), Vanilla JavaScript
- **Development & Notebooks**: Jupyter Notebooks (`.ipynb` included for models and rejection analysis)

---

## 📂 Project Structure

```
├── CODE/
│   └── Acne_Type_Classification/
│       ├── Acne_Type_Classification/  # Core Django configuration files
│       ├── admins/                    # Admin app logic & models
│       ├── users/                     # User management, OTP & authentication logic
│       ├── templates/                 # Glassmorphism HTML templates
│       ├── static/                    # Custom CSS, JS, images & video assets
│       ├── media/                     # Evaluation graphs, confusion matrices & models
│       │   ├── models/                # Pre-trained yolo and rejection model files
│       │   ├── confusion_matrices/    # Model performance evaluations
│       │   └── graphs/                # Training performance plots (ResNet vs VGG)
│       ├── db.sqlite3                 # Local Django database (git-ignored)
│       └── requirements.txt           # Python dependencies
├── .gitignore                         # Configured git exclusions
└── README.md                          # Documentation (this file)
```

---

## 🚀 Setup and Installation

### Prerequisites
- Python 3.8 or higher
- Git

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd <repository-directory>
```

### 2. Set Up a Virtual Environment
```bash
python -m venv venv
# On Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r CODE/Acne_Type_Classification/requirements.txt
```

### 4. Apply Database Migrations
```bash
python CODE/Acne_Type_Classification/manage.py migrate
```

### 5. Start the Development Server
```bash
python CODE/Acne_Type_Classification/manage.py runserver
```
Visit the application at `http://127.0.0.1:8000` in your web browser.

---

## 📊 Evaluation and Performance Metrics
The system provides built-in visual analytics and logs located in the `media/` directory, illustrating training accuracy, validation curves, and confusion matrices comparing baseline models with synthetic DCGAN-augmented performance.

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
