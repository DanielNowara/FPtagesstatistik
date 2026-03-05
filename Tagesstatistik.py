import streamlit as st
import pandas as pd
import os
import json
from datetime import date, timedelta
import calendar
import plotly.express as px

# --- KONFIGURATION ---
st.set_page_config(page_title="Tagesstatistik", page_icon="🏋️‍♂️", layout="wide")

DATA_FILE = "tagesstatistik_daten.csv"
ZIELE_FILE = "ziele_daten.csv"
SETTINGS_FILE = "settings.json"

# Standard-Layout
DEFAULT_LAYOUT = [
    {"id": "beratungen", "Feldname": "Beratungen heute", "Kategorie": "Vertrieb & Abos", "Sortierung": 10},
    {"id": "abos_heute", "Feldname": "Abos gesamt heute", "Kategorie": "Vertrieb & Abos", "Sortierung": 20},
    {"id": "online_abos_heute", "Feldname": "davon Online-Abos", "Kategorie": "Vertrieb & Abos", "Sortierung": 30},
    {"id": "abos_12m", "Feldname": "davon 12 Monate", "Kategorie": "Vertrieb & Abos", "Sortierung": 40},
    {"id": "abos_1m", "Feldname": "davon 1 Monat", "Kategorie": "Vertrieb & Abos", "Sortierung": 50},
    {"id": "abos_fitnessplus", "Feldname": "davon Fitness+", "Kategorie": "Vertrieb & Abos", "Sortierung": 60},
    {"id": "leads_intern", "Feldname": "Leads intern (VIP/10er)", "Kategorie": "Leads & Calls", "Sortierung": 10},
    {"id": "sonstige_leads", "Feldname": "Sonstige Leads", "Kategorie": "Leads & Calls", "Sortierung": 20},
    {"id": "termine_callin", "Feldname": "Termine durch Call-in", "Kategorie": "Leads & Calls", "Sortierung": 30},
    {"id": "termine_callout", "Feldname": "Termine durch Call-out", "Kategorie": "Leads & Calls", "Sortierung": 40},
    {"id": "termine_callout_plus", "Feldname": "davon Fitness+ (Call-out)", "Kategorie": "Leads & Calls", "Sortierung": 50},
    {"id": "checkups_heute", "Feldname": "Check Ups heute", "Kategorie": "Sonstiges", "Sortierung": 10},
    {"id": "sonstiges", "Feldname": "Sonstiges (PT etc.)", "Kategorie": "Sonstiges", "Sortierung": 20},
    {"id": "checkins", "Feldname": "Check-Ins", "Kategorie": "Sonstiges", "Sortierung": 30}
]

# --- DATEN-FUNKTIONEN ---
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"studios": ["Cham", "Studio 2"], "layout": DEFAULT_LAYOUT}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Datum'] = pd.to_datetime(df['Datum']).dt.date
        return df
    return pd.DataFrame()

def save_data(new_data_dict):
    df = load_data()
    
    if not df.empty and 'Datum' in df.columns and 'Studio' in df.columns:
        mask = (df['Datum'] == new_data_dict['Datum']) & (df['Studio'] == new_data_dict['Studio'])
        if mask.any():
            for key, value in new_data_dict.items():
                df.loc[mask, key] = value
        else:
            new_df = pd.DataFrame([new_data_dict])
            df = pd.concat([df, new_df], ignore_index=True)
    else:
        df = pd.DataFrame([new_data_dict])
        
    df.to_csv(DATA_FILE, index=False)

def load_ziele():
    if os.path.exists(ZIELE_FILE):
        return pd.read_csv(ZIELE_FILE)
    return pd.DataFrame(columns=[
        "Monat_Jahr", "Studio", "Monatsziel_Abos", "Auslaufende_Abos", 
        "Ziel_VIP_Leads_Woche", "Ziel_CallOut_Woche", "Ziel_CheckUps_Woche"
    ])

def save_ziele(neue_ziele_dict):
    df = load_ziele()
    mask = (df['Monat_Jahr'] == neue_ziele_dict['Monat_Jahr']) & (df['Studio'] == neue_ziele_dict['Studio'])
    if mask.any():
        df.loc[mask, :] = pd.DataFrame([neue_ziele_dict]).values
    else:
        new_df = pd.DataFrame([neue_ziele_dict])
        df = pd.concat([df, new_df], ignore_index=True)
    df.to_csv(ZIELE_FILE, index=False)

settings = load_settings()

# --- APP STRUKTUR ---
st.title("🏋️‍♂️ Tagesstatistik Fitnesspoint")

tab1, tab2, tab3 = st.tabs(["📝 Tagesabschluss", "⚙️ Admin & Setup", "📊 Auswertung & Dashboard"])

# ==========================================
# TAB 1: TAGESABSCHLUSS
# ==========================================
with tab1:
    st.markdown('*"Nur wer sein Ziel kennt, findet den Weg dorthin"*')
    
    col_date, col_studio = st.columns(2)
    with col_date:
        eingabe_datum = st.date_input("Datum", date.today())
    with col_studio:
        if not settings["studios"]:
            st.warning("Bitte lege zuerst ein Studio im Admin-Bereich an.")
            st.stop()
        studio = st.selectbox("Studio", settings["studios"])

    jahr, monat = eingabe_datum.year, eingabe_datum.month
    monat_jahr_str = f"{jahr}-{monat:02d}"
    kw = eingabe_datum.isocalendar()[1]
    tage_im_monat = calendar.monthrange(jahr, monat)[1]
    
    df_tagesdaten = load_data()
    df_ziele = load_ziele()
    
    aktuelle_ziele = df_ziele[(df_ziele['Monat_Jahr'] == monat_jahr_str) & (df_ziele['Studio'] == studio)]
    if aktuelle_ziele.empty:
        ziel_abos, ziel_auslaufend, ziel_vip_woche, ziel_callout_woche, ziel_checkups_woche = 0, 0, 35, 21, 42
    else:
        ziel_abos = aktuelle_ziele.iloc[0]['Monatsziel_Abos']
        ziel_auslaufend = aktuelle_ziele.iloc[0]['Auslaufende_Abos']
        ziel_vip_woche = aktuelle_ziele.iloc[0]['Ziel_VIP_Leads_Woche']
        ziel_callout_woche = aktuelle_ziele.iloc[0]['Ziel_CallOut_Woche']
        ziel_checkups_woche = aktuelle_ziele.iloc[0]['Ziel_CheckUps_Woche']

    # --- MATHE: BERECHNUNG DES TAGESZIELS ---
    werktage_im_monat = sum(1 for d in range(1, tage_im_monat + 1) if calendar.weekday(jahr, monat, d) < 5)
    wochenendtage_im_monat = tage_im_monat - werktage_im_monat
            
    nenner = werktage_im_monat + 0.5 * wochenendtage_im_monat
    ziel_werktag = ziel_abos / nenner if nenner > 0 else 0
    ziel_wochenende = ziel_werktag * 0.5
    
    ist_wochenende = eingabe_datum.weekday() >= 5
    heutiges_soll_ziel = ziel_wochenende if ist_wochenende else ziel_werktag
    
    erwartete_abos_bisher = sum(ziel_wochenende if calendar.weekday(jahr, monat, d) >= 5 else ziel_werktag for d in range(1, eingabe_datum.day + 1))

    if not df_tagesdaten.empty and 'Datum' in df_tagesdaten.columns:
        df_monat = df_tagesdaten[(df_tagesdaten['Studio'] == studio) & 
                                 (pd.to_datetime(df_tagesdaten['Datum']).dt.year == jahr) & 
                                 (pd.to_datetime(df_tagesdaten['Datum']).dt.month == monat) &
                                 (df_tagesdaten['Datum'] < eingabe_datum)]
        
        abos_bisher_monat = df_monat['Abos_heute'].sum() if 'Abos_heute' in df_monat else 0
        online_bisher_monat = df_monat['Online_Abos_heute'].sum() if 'Online_Abos_heute' in df_monat else 0

        df_woche = df_tagesdaten[(df_tagesdaten['Studio'] == studio) & 
                                 (pd.to_datetime(df_tagesdaten['Datum']).dt.isocalendar().week == kw) &
                                 (pd.to_datetime(df_tagesdaten['Datum']).dt.year == jahr) &
                                 (df_tagesdaten['Datum'] < eingabe_datum)]
        
        leads_bisher_woche = df_woche['Leads_intern'].sum() if 'Leads_intern' in df_woche else 0
        callout_bisher_woche = df_woche['Termine_CallOut_heute'].sum() if 'Termine_CallOut_heute' in df_woche else 0
        checkups_bisher_woche = df_woche['CheckUps_heute'].sum() if 'CheckUps_heute' in df_woche else 0
    else:
        abos_bisher_monat = online_bisher_monat = leads_bisher_woche = callout_bisher_woche = checkups_bisher_woche = 0

    inputs = {}
    layout_df = pd.DataFrame(settings["layout"])
    layout_df = layout_df[layout_df["id"] != "tagesziel_erreicht"]
    layout_df = layout_df.sort_values(by=["Sortierung"])
    
    gewuenschte_reihenfolge = ["Vertrieb & Abos", "Leads & Calls", "Sonstiges"]
    vorhandene_kat = layout_df["Kategorie"].unique()
    kategorien = [k for k in gewuenschte_reihenfolge if k in vorhandene_kat]
    kategorien.extend([k for k in vorhandene_kat if k not in gewuenschte_reihenfolge])

    st.info(f"🎯 **Automatisch berechnetes Tagesziel für heute:** {heutiges_soll_ziel:.1f} Abos")

    with st.form("tagesstatistik_form"):
        st.subheader("📝 1. Tägliche Statistiken")
        
        for kat in kategorien:
            st.write(f"**{kat}**")
            felder_in_kat = layout_df[layout_df["Kategorie"] == kat]
            
            cols = st.columns(3)
            for idx, row in enumerate(felder_in_kat.itertuples()):
                col = cols[idx % 3]
                with col:
                    inputs[row.id] = st.number_input(row.Feldname, min_value=0, step=1)
            st.divider()

        st.write("**Bemerkungen**")
        kommentar = st.text_area("Kommentar zum Tag (optional)")
        st.divider()

        submitted = st.form_submit_button("💾 Speichern & Bericht generieren", use_container_width=True)

        if submitted:
            def get_val(fid): return inputs.get(fid, 0)
            abos_heute = get_val("abos_heute")
            tagesziel_erreicht = "JA" if abos_heute >= heutiges_soll_ziel else "NEIN"
            ja_box = "☑" if tagesziel_erreicht == "JA" else "☐"
            nein_box = "☑" if tagesziel_erreicht == "NEIN" else "☐"
            
            new_data = {
                "Datum": eingabe_datum, "Studio": studio, "Kommentar": kommentar,
                "Beratungen_heute": get_val("beratungen"), "Abos_heute": abos_heute, 
                "Online_Abos_heute": get_val("online_abos_heute"), "Abos_12M": get_val("abos_12m"), 
                "Abos_1M": get_val("abos_1m"), "Abos_FitnessPlus": get_val("abos_fitnessplus"),
                "Leads_intern": get_val("leads_intern"), "Sonstige_Leads": get_val("sonstige_leads"), 
                "Termine_CallIn": get_val("termine_callin"), "Termine_CallOut_heute": get_val("termine_callout"), 
                "Termine_CallOut_FitnessPlus": get_val("termine_callout_plus"), "CheckUps_heute": get_val("checkups_heute"),
                "Sonstiges": get_val("sonstiges"), "CheckIns": get_val("checkins"), "Tagesziel_erreicht": tagesziel_erreicht
            }
            save_data(new_data)
            st.success("✅ Erfolgreich gespeichert! (Bestehender Eintrag wurde überschrieben, falls vorhanden)")

            final_abos_monat = abos_bisher_monat + abos_heute
            final_online_monat = online_bisher_monat + get_val("online_abos_heute")
            final_vip_woche = leads_bisher_woche + get_val("leads_intern")
            final_callout_woche = callout_bisher_woche + get_val("termine_callout")
            final_checkups_woche = checkups_bisher_woche + get_val("checkups_heute")

            # HTML BERICHT OHNE EINRÜCKUNG (Damit Streamlit es als echtes HTML erkennt)
            html_bericht = f"""<div style="background-color: white; color: black; padding: 25px; border: 2px solid #333; border-radius: 8px; font-family: Arial, sans-serif; max-width: 600px; margin: auto; box-shadow: 2px 2px 12px rgba(0,0,0,0.1);">
    <h2 style="text-align: center; margin-top: 0; padding-bottom: 10px; border-bottom: 2px solid black;">
        Tagesstatistik Fitnesspoint {studio}
    </h2>
    <p style="font-size: 16px; margin-bottom: 20px;"><strong>Datum:</strong> {eingabe_datum.strftime('%d.%m.%Y')}</p>

    <h3 style="background-color: #f0f0f0; padding: 5px 10px; border-left: 4px solid #d9232a; margin-bottom: 10px;">Monatsziele:</h3>
    <table style="width: 100%; margin-bottom: 15px; font-size: 14px;">
        <tr><td style="padding: 3px 0;">Monatsziel (Abos):</td><td style="text-align: right;"><strong>{ziel_abos}</strong></td></tr>
        <tr><td style="padding: 3px 0;">Abos (Monat):</td><td style="text-align: right;"><strong>{final_abos_monat}</strong></td></tr>
        <tr><td style="padding: 3px 0; padding-left: 20px; color: #555;">davon Online-Abos:</td><td style="text-align: right;">{final_online_monat}</td></tr>
        <tr><td style="padding: 3px 0;">Auslaufende Abos:</td><td style="text-align: right;"><strong>{ziel_auslaufend}</strong></td></tr>
    </table>

    <h3 style="background-color: #f0f0f0; padding: 5px 10px; border-left: 4px solid #d9232a; margin-bottom: 10px;">Tagesziel:</h3>
    <table style="width: 100%; margin-bottom: 15px; font-size: 14px;">
        <tr><td style="padding: 3px 0;">Beratungen heute:</td><td style="text-align: right;"><strong>{new_data['Beratungen_heute']}</strong></td></tr>
        <tr><td style="padding: 3px 0; padding-top: 10px;"><strong>Abos gesamt heute:</strong></td><td style="text-align: right; padding-top: 10px;"><strong>{abos_heute}</strong></td></tr>
        <tr><td style="padding: 3px 0; padding-left: 20px; color: #555;">davon Online-Abos:</td><td style="text-align: right;">{new_data['Online_Abos_heute']}</td></tr>
        <tr><td style="padding: 3px 0; padding-left: 20px; color: #555;">davon 12 Monate:</td><td style="text-align: right;">{new_data['Abos_12M']}</td></tr>
        <tr><td style="padding: 3px 0; padding-left: 20px; color: #555;">davon 1 Monat:</td><td style="text-align: right;">{new_data['Abos_1M']}</td></tr>
        <tr><td style="padding: 3px 0; padding-left: 20px; color: #555;">davon Fitness+:</td><td style="text-align: right;">{new_data['Abos_FitnessPlus']}</td></tr>
    </table>

    <h3 style="background-color: #f0f0f0; padding: 5px 10px; border-left: 4px solid #d9232a; margin-bottom: 10px;">EOAs Wochenziele (Mo-So):</h3>
    <table style="width: 100%; margin-bottom: 15px; font-size: 14px;">
        <tr><td style="padding: 3px 0;">VIP-Leads (Ziel {ziel_vip_woche}):</td><td style="text-align: right;"><strong>{final_vip_woche}</strong></td></tr>
        <tr><td style="padding: 3px 0;">Termine Call-out (Ziel {ziel_callout_woche}):</td><td style="text-align: right;"><strong>{final_callout_woche}</strong></td></tr>
        <tr><td style="padding: 3px 0;">Check Ups (Ziel: {ziel_checkups_woche}):</td><td style="text-align: right;"><strong>{final_checkups_woche}</strong></td></tr>
    </table>

    <hr style="border: 0; border-top: 1px solid #ccc; margin: 20px 0;">

    <table style="width: 100%; margin-bottom: 15px; font-size: 14px;">
        <tr><td style="padding: 4px 0;">Leads intern (VIP/10er Karte):</td><td style="text-align: right;"><strong>{new_data['Leads_intern']}</strong></td></tr>
        <tr><td style="padding: 4px 0;">Sonstige Leads:</td><td style="text-align: right;"><strong>{new_data['Sonstige_Leads']}</strong></td></tr>
        <tr><td style="padding: 4px 0;">Termine durch Call-in:</td><td style="text-align: right;"><strong>{new_data['Termine_CallIn']}</strong></td></tr>
        <tr><td style="padding: 4px 0;">Termine durch Call-out:</td><td style="text-align: right;"><strong>{new_data['Termine_CallOut_heute']}</strong></td></tr>
        <tr><td style="padding: 3px 0; padding-left: 20px; color: #555;">davon Fitness+:</td><td style="text-align: right;">{new_data['Termine_CallOut_FitnessPlus']}</td></tr>
        <tr><td style="padding: 4px 0;">Sonstiges (z.B: Check Ups / PT):</td><td style="text-align: right;"><strong>{new_data['Sonstiges']}</strong></td></tr>
        <tr><td style="padding: 4px 0;">Check-Ins:</td><td style="text-align: right;"><strong>{new_data['CheckIns']}</strong></td></tr>
    </table>

    <div style="background-color: #f9f9f9; padding: 15px; border: 1px solid #ddd; text-align: center; margin-top: 20px;">
        <strong style="font-size: 16px;">TAGESZIEL ERREICHT:</strong> 
        <span style="margin-left: 15px; font-size: 18px;">JA: {ja_box}</span>
        <span style="margin-left: 15px; font-size: 18px;">NEIN: {nein_box}</span>
    </div>
    
    <p style="text-align: center; font-style: italic; font-size: 12px; margin-top: 20px; color: #666;">
        "Nur wer sein Ziel kennt, findet den Weg dorthin"
    </p>
</div>
"""
            
            st.info("📸 **Fertig! Du kannst diesen Bericht jetzt einfach abfotografieren oder einen Screenshot machen und ihn in WhatsApp teilen:**")
            st.markdown(html_bericht, unsafe_allow_html=True)

# ==========================================
# TAB 2: ADMIN & SETUP
# ==========================================
with tab2:
    st.header("⚙️ System Setup & Ziele")
    
    st.subheader("🏢 Studios verwalten")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        neues_studio = st.text_input("Neues Studio hinzufügen:")
        if st.button("Studio anlegen"):
            if neues_studio and neues_studio not in settings["studios"]:
                settings["studios"].append(neues_studio)
                save_settings(settings)
                st.success(f"{neues_studio} wurde hinzugefügt!")
                st.rerun()
    with col_s2:
        studios_zu_loeschen = st.multiselect("Studios entfernen:", settings["studios"])
        if st.button("Ausgewählte löschen"):
            for s in studios_zu_loeschen:
                settings["studios"].remove(s)
            save_settings(settings)
            st.success("Gelöscht!")
            st.rerun()

    st.divider()

    st.subheader("📋 Formular-Layout anpassen")
    df_layout = pd.DataFrame(settings["layout"])
    df_layout = df_layout[df_layout["id"] != "tagesziel_erreicht"]
    
    edited_layout = st.data_editor(
        df_layout, 
        disabled=["id", "Feldname"], 
        hide_index=True,
        column_config={
            "Kategorie": st.column_config.TextColumn("Kategorie (Überschrift)"),
            "Sortierung": st.column_config.NumberColumn("Sortierung (10, 20, 30...)")
        },
        use_container_width=True
    )
    
    if st.button("💾 Layout Änderungen speichern"):
        settings["layout"] = edited_layout.to_dict('records')
        save_settings(settings)
        st.success("Layout erfolgreich aktualisiert!")

    st.divider()

    st.subheader("🎯 Monats- & Wochenziele einstellen")
    with st.form("admin_ziele_form"):
        col1, col2 = st.columns(2)
        with col1:
            admin_studio = st.selectbox("Studio auswählen", settings["studios"])
        with col2:
            admin_monat = st.date_input("Für welchen Monat? (Tag ist egal)", date.today())
            
        admin_mj_str = f"{admin_monat.year}-{admin_monat.month:02d}"
        
        c1, c2 = st.columns(2)
        mit_c1 = c1.number_input("Monatsziel (Abos)", min_value=0, step=1, value=50)
        mit_c2 = c2.number_input("Auslaufende Abos", min_value=0, step=1, value=10)
        
        c3, c4, c5 = st.columns(3)
        mit_c3 = c3.number_input("VIP-Leads Ziel (Woche)", min_value=0, step=1, value=35)
        mit_c4 = c4.number_input("Termine Call-out Ziel (Woche)", min_value=0, step=1, value=21)
        mit_c5 = c5.number_input("Check Ups Ziel (Woche)", min_value=0, step=1, value=42)
        
        if st.form_submit_button("Ziele speichern"):
            ziele_dict = {
                "Monat_Jahr": admin_mj_str, "Studio": admin_studio, 
                "Monatsziel_Abos": mit_c1, "Auslaufende_Abos": mit_c2,
                "Ziel_VIP_Leads_Woche": mit_c3, "Ziel_CallOut_Woche": mit_c4, 
                "Ziel_CheckUps_Woche": mit_c5
            }
            save_ziele(ziele_dict)
            st.success(f"Ziele für {admin_studio} ({admin_monat.strftime('%m/%Y')}) gespeichert!")

# ==========================================
# TAB 3: AUSWERTUNG & DASHBOARD
# ==========================================
with tab3:
    st.header("📊 Auswertung & Dashboard")
    df_auswertung = load_data()
    
    if df_auswertung.empty:
        st.info("Noch keine Daten vorhanden. Trage zuerst Statistiken ein.")
    else:
        df_auswertung['Datum'] = pd.to_datetime(df_auswertung['Datum']).dt.date
        
        st.subheader("🔍 Daten filtern")
        col_f1, col_f2 = st.columns(2)
        
        min_date = df_auswertung['Datum'].min()
        max_date = df_auswertung['Datum'].max()
        
        with col_f1:
            default_start = max_date - timedelta(days=30) if (max_date - timedelta(days=30)) >= min_date else min_date
            selected_dates = st.date_input("Zeitraum auswählen", value=(default_start, max_date), min_value=min_date, max_value=max_date)
            
        with col_f2:
            alle_studios = sorted(df_auswertung['Studio'].unique().tolist())
            selected_studios = st.multiselect("Studio(s) auswählen", options=alle_studios, default=alle_studios)

        if len(selected_dates) == 2:
            start_date, end_date = selected_dates
            
            mask = (df_auswertung['Datum'] >= start_date) & (df_auswertung['Datum'] <= end_date) & (df_auswertung['Studio'].isin(selected_studios))
            df_filtered = df_auswertung[mask]
            
            if not df_filtered.empty:
                st.divider()
                
                st.subheader("💡 Kennzahlen im gewählten Zeitraum")
                
                sum_beratungen = df_filtered['Beratungen_heute'].sum() if 'Beratungen_heute' in df_filtered else 0
                sum_abos = df_filtered['Abos_heute'].sum() if 'Abos_heute' in df_filtered else 0
                sum_leads = (df_filtered['Leads_intern'].sum() + df_filtered['Sonstige_Leads'].sum()) if 'Leads_intern' in df_filtered else 0
                
                abschlussquote = (sum_abos / sum_beratungen * 100) if sum_beratungen > 0 else 0.0
                
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                kpi1.metric("🤝 Beratungen", f"{sum_beratungen:.0f}")
                kpi2.metric("📝 Abos (Gesamt)", f"{sum_abos:.0f}")
                kpi3.metric("🎯 Abschlussquote", f"{abschlussquote:.1f} %")
                kpi4.metric("🔥 Leads (Gesamt)", f"{sum_leads:.0f}")
                
                st.divider()
                
                st.subheader("📈 Detaillierte Auswertung (Grafik)")
                
                numerische_spalten = df_filtered.select_dtypes(include=['number']).columns.tolist()
                auswahl_wert = st.selectbox("Welchen Wert möchtest du auswerten?", numerische_spalten, 
                                            index=numerische_spalten.index('Abos_heute') if 'Abos_heute' in numerische_spalten else 0)
                
                fig = px.bar(df_filtered, x="Datum", y=auswahl_wert, color="Studio", 
                             title=f"Verlauf von '{auswahl_wert}'", barmode="group",
                             labels={auswahl_wert: "Anzahl", "Datum": "Tag"})
                
                fig.update_xaxes(type='category')
                st.plotly_chart(fig, use_container_width=True)
                
                st.divider()
                
                st.subheader("📋 Gefilterte Rohdaten (Tabelle)")
                st.dataframe(df_filtered.sort_values(by="Datum", ascending=False), use_container_width=True)
                
            else:
                st.warning("Für den ausgewählten Zeitraum und die ausgewählten Studios liegen leider keine Daten vor.")
        else:
            st.info("Bitte wähle ein Start- UND Enddatum im Kalender aus.")

