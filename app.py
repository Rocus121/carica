import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
import zipfile
import tempfile
import os

# Connessione al database SQLite
conn = sqlite3.connect("cv_database.db", check_same_thread=False)
cursor = conn.cursor()

# Creazione della tabella se non esiste
cursor.execute("""
CREATE TABLE IF NOT EXISTS cv_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    email TEXT,
    cv BLOB
)
""")
conn.commit()

# Funzione per creare un file ZIP con tutti i CV
def create_all_cv_zip():
    # Crea un file temporaneo per il ZIP
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
        zip_path = temp_zip.name
    
    # Crea il file ZIP
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # Recupera tutti i CV dal database
        cursor.execute("SELECT id, nome, email, cv FROM cv_data")
        all_records = cursor.fetchall()
        
        for record in all_records:
            cv_id, nome, email, cv_data = record
            # Crea un nome file per ogni CV
            file_name = f"{cv_id}_{nome}_CV.pdf"
            # Aggiungi il CV al file ZIP
            zipf.writestr(file_name, cv_data)
    
    # Leggi il file ZIP
    with open(zip_path, 'rb') as f:
        zip_data = f.read()
    
    # Elimina il file temporaneo
    os.unlink(zip_path)
    
    return zip_data

# Funzione per esportare i dati in formato CSV
def create_data_csv():
    cursor.execute("SELECT id, nome, email FROM cv_data")
    records = cursor.fetchall()
    
    df = pd.DataFrame(records, columns=["ID", "Nome", "Email"])
    csv = df.to_csv(index=False).encode('utf-8')
    
    return csv

# Interfaccia Streamlit
st.title("Raccolta CV")

# Crea due sezioni con le tabs
tab1, tab2 = st.tabs(["Carica CV", "Amministrazione"])

with tab1:
    # Form per l'inserimento dei dati
    with st.form("cv_form"):
        nome = st.text_input("Nome")
        mail = st.text_input("Email")
        file_cv = st.file_uploader("Carica il tuo CV (PDF)", type=["pdf"])
        submit = st.form_submit_button("Invia")

        if submit and nome and mail and file_cv:
            # Legge il file in formato binario
            cv_data = file_cv.read()

            # Inserisce i dati nel database
            cursor.execute("INSERT INTO cv_data (nome, email, cv) VALUES (?, ?, ?)", (nome, mail, cv_data))
            conn.commit()
            
            st.success("Dati salvati con successo!")

with tab2:
    # Sezione di amministrazione
    st.write("### Pannello di Amministrazione")
    
    # Opzioni di download
    col1, col2 = st.columns(2)
    
    with col1:
        # Bottone per scaricare tutti i CV in un file ZIP
        zip_data = create_all_cv_zip()
        st.download_button(
            label="📥 Scarica tutti i CV (ZIP)",
            data=BytesIO(zip_data),
            file_name="tutti_i_cv.zip",
            mime="application/zip"
        )
    
    with col2:
        # Bottone per scaricare i dati come CSV
        csv_data = create_data_csv()
        st.download_button(
            label="📥 Scarica dati (CSV)",
            data=BytesIO(csv_data),
            file_name="dati_cv.csv",
            mime="text/csv"
        )
    
    # Recupero dei dati dal database per visualizzazione
    cursor.execute("SELECT id, nome, email FROM cv_data")
    records = cursor.fetchall()

    if records:
        st.write("### Elenco CV caricati")
        
        # Creazione di un DataFrame per visualizzare i dati
        df = pd.DataFrame(records, columns=["ID", "Nome", "Email"])
        st.dataframe(df)

        # Pulsanti per scaricare i singoli CV
        st.write("### Download singoli CV")
        for row in records:
            cv_id = row[0]
            nome = row[1]
            
            cursor.execute("SELECT cv FROM cv_data WHERE id = ?", (cv_id,))
            file_data = cursor.fetchone()[0]
            
            st.download_button(
                label=f"Scarica CV di {nome}",
                data=BytesIO(file_data),
                file_name=f"{nome}_CV.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Nessun CV presente nel database.")

    # Pulsante per scaricare l'intero database
    st.write("### Download Database")
    with open("cv_database.db", "rb") as f:
        st.download_button(
            label="📥 Scarica Database completo",
            data=f,
            file_name="cv_database.db",
            mime="application/octet-stream"
        )

# Chiude la connessione al database quando l'app viene chiusa
conn.close()