# ⚡ Short-Term Load Forecasting Using LSTM and Bi-LSTM with Interactive Dashboard Integration

## 📌 Overview

This project focuses on **Short-Term Load Forecasting (STLF)** using deep learning techniques such as **LSTM** and **Bi-LSTM** models. The system predicts future energy consumption patterns for academic buildings and visualizes the results through an interactive real-time dashboard.

The project aims to improve forecasting accuracy, enhance energy monitoring, and support smarter energy management using machine learning and data visualization techniques.

---

# 🚀 Features

* 📈 Short-term energy load forecasting
* 🤖 LSTM and Bi-LSTM model implementation
* 🔄 Shift-based temporal preprocessing
* 🌐 Interactive real-time dashboard
* 🏢 Multi-building energy monitoring
* 📊 Actual vs Predicted trend comparison
* 📉 Model performance evaluation
* ⚡ User-friendly visualization interface

---

# 🛠️ Tech Stack

### Programming Language

* Python

### Machine Learning / Deep Learning

* TensorFlow
* Keras
* Scikit-learn

### Data Processing

* Pandas
* NumPy

### Visualization

* Matplotlib
* Plotly

### Dashboard / Frontend

* Streamlit

### Database

* SQL

---

# 🧠 Models Used

## 1️⃣ LSTM (Long Short-Term Memory)

LSTM is a type of recurrent neural network designed to learn temporal dependencies from sequential data. It is effective for time-series forecasting due to its ability to retain long-term information.

## 2️⃣ Bi-LSTM (Bidirectional LSTM)

Bi-LSTM processes data in both forward and backward directions, allowing the model to capture more contextual information and improve prediction capability.

## 3️⃣ Shift-Based Preprocessing

A shift method was applied to create lagged features from historical load data, helping the models better learn temporal patterns.

---

# 📂 Dataset

The dataset consists of historical energy consumption data collected from multiple academic buildings.

### Data Includes:

* Timestamp
* Energy Consumption Values
* Building-wise Load Data

---

# 📊 Dashboard Features

The Streamlit dashboard provides:

* Real-time prediction visualization
* Actual vs Predicted comparison graphs
* Building-wise analysis
* Model comparison
* Interactive and responsive UI

---

# 📈 Evaluation Metrics

The models were evaluated using:

* Mean Absolute Error (MAE)
* Mean Squared Error (MSE)
* R² Score

---

# ⚠️ Challenges Faced

* Highly fluctuating academic building load patterns
* Sudden spikes and irregular consumption trends
* Model overfitting in Bi-LSTM
* Difficulty in capturing abrupt load variations

---

# 🔮 Future Improvements

* Integration of weather data
* Occupancy-based prediction
* Renewable energy forecasting
* Real-time adaptive learning
* Transformer-based forecasting models

---

# 💡 Key Learnings

Through this project, I gained practical experience in:

* Time-series forecasting
* Deep learning model development
* Feature engineering
* Dashboard development
* Data visualization
* Smart energy analytics

---

# ▶️ How to Run the Project

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/your-repository-name.git
```

## 2️⃣ Navigate to the Project Folder

```bash
cd your-repository-name
```

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

## 4️⃣ Run the Streamlit Dashboard

```bash
streamlit run app.py
```

---

# 👨‍💻 Author

**Yashovardhan Appakaya**
Vellore Institute of Technology, Vellore

---

# 🙏 Acknowledgement

I would like to sincerely thank **Prof. Meikandesivam S** for his continuous guidance, support, and encouragement throughout the development of this project.

---

# 📌 Keywords

`Machine Learning` `Deep Learning` `LSTM` `Bi-LSTM` `Streamlit` `Load Forecasting` `Energy Analytics` `Time-Series Forecasting` `Smart Grid`
