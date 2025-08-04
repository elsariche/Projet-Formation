import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# --- Configuration de la page ---
st.set_page_config(layout="wide", page_title="Analyse du World Happiness Report", page_icon="🌍",  initial_sidebar_state="expanded")


# --- Configuration des chemins de fichiers ---
FILE_PATH_WHR = "world-happiness-report.csv"
FILE_PATH_MERGE_ID = "Merge_ID_Year_Country.csv"
FILE_PATH_WHR_2020 = "WHR20_DataForFigure2.1.xlsx"
FILE_PATH_WHR_2021 = "world-happiness-report-2021.csv"
FILE_PATH_GDP = "Logged_GDP_per_Capita_2005-2023.xlsx"
FILE_PATH_LIFE = "Healthy Life Expectancy 2000-2021.csv"

WHR_2005_2020 = pd.read_csv(FILE_PATH_WHR, sep=',')
WHR_2021 = pd.read_csv(FILE_PATH_WHR_2021, sep=',')

# --- Fonction de chargement et de nettoyage des données (avec cache Streamlit) ---
@st.cache_data
def load_and_preprocess_data():
    with st.spinner('Chargement et prétraitement des données...'):

        # Initial Load
        df = pd.read_csv(FILE_PATH_WHR, sep=',')

        # Add 'id' column for merging
        df['year'] = df['year'].astype('str')
        df['id'] = df['year'] + "-" + df['Country name']

        # Load ID base
        ID = pd.read_csv(FILE_PATH_MERGE_ID, sep=';')

        # Merge df & ID base
        merge_df = ID.merge(df, on='id', how='outer')
        merge_df = merge_df.drop(columns=['Country name_y', 'year_y'])
        merge_df = merge_df.rename(columns={'year_x': 'year', 'Country name_x': 'Country name'})

        # Load 2020 & 2021 data
        df_2020 = pd.read_excel(FILE_PATH_WHR_2020)
        df_2020['id'] = "2020" + "-" + df_2020['Country name']
        df_2020['year'] = "2020" # Assurer le type str

        df_2021 = pd.read_csv(FILE_PATH_WHR_2021, sep=',')
        df_2021['id'] = "2021" + "-" + df_2021['Country name']
        df_2021['year'] = "2021" # Assurer le type str

        df_concat_2020_2021 = pd.concat([df_2021, df_2020], ignore_index=True)
        df_concat_2020_2021 = df_concat_2020_2021[[
            'id', 'year', 'Country name', 'Regional indicator', 'Ladder score',
            'Logged GDP per capita', 'Social support', 'Healthy life expectancy',
            'Freedom to make life choices', 'Generosity', 'Perceptions of corruption'
        ]]

        # Prepare merge_df for final merge
        merge_df_temp = merge_df.rename(columns={
            'Log GDP per capita': 'Logged GDP per capita',
            'Healthy life expectancy at birth': 'Healthy life expectancy'
        }).copy() # Utiliser .copy() pour éviter SettingWithCopyWarning

        # Ensure 'year' is consistent type before merging
        merge_df_temp['year'] = merge_df_temp['year'].astype(str)
        df_concat_2020_2021['year'] = df_concat_2020_2021['year'].astype(str)


        df_final_merge = pd.merge(merge_df_temp, df_concat_2020_2021, on=['id', 'year', 'Country name'], how='outer', suffixes=('_x', '_y'))

        # Fill NaN from new data
        for col_name in ['Logged GDP per capita', 'Social support', 'Healthy life expectancy',
                         'Freedom to make life choices', 'Generosity', 'Perceptions of corruption']:
            df_final_merge[col_name] = df_final_merge[f'{col_name}_x'].fillna(df_final_merge[f'{col_name}_y'])
        df_final_merge['Life Ladder'] = df_final_merge['Life Ladder'].fillna(df_final_merge['Ladder score'])

        # Drop duplicate columns
        df_final_merge = df_final_merge.drop(columns=[col for col in df_final_merge.columns if '_x' in col or '_y' in col or col == 'Ladder score'])

        # Reorder columns (définir reorder ici car c'est nécessaire pour le traitement)
        reorder = ['id', 'year', 'Country name', 'ISO-alpha3 Code', 'Regional indicator', 'Life Ladder', 'Logged GDP per capita',
                   'Social support', 'Healthy life expectancy', 'Freedom to make life choices', 'Generosity', 'Perceptions of corruption',
                   'Positive affect', 'Negative affect']
        df_final_merge = df_final_merge[reorder]

        # Enrich Regional indicator
        df_final_merge['Regional indicator'] = df_final_merge['Regional indicator'].fillna(df_final_merge.groupby('Country name')['Regional indicator'].transform('first'))

        # Fill specific missing regions
        pays_region = {
            'Angola': 'Sub-Saharan Africa', 'Belize': 'Latin America and Caribbean', 'Bhutan': 'South Asia',
            'Cuba': 'Latin America and Caribbean', 'Djibouti': 'Sub-Saharan Africa', 'Guyana': 'Latin America and Caribbean',
            'North Macedonia': 'Central and Eastern Europe', 'Oman': 'Middle East and North Africa',
            'Qatar': 'Middle East and North Africa', 'Somalia': 'Middle East and North Africa',
            'Somaliland region': 'Middle East and North Africa', 'Sudan': 'Sub-Saharan Africa',
            'Suriname': 'Latin America and Caribbean', 'Syria': 'Middle East and North Africa'
        }
        df_final_merge['Regional indicator'] = df_final_merge['Regional indicator'].fillna(df_final_merge['Country name'].map(pays_region))

        # Enrich ISO-alpha3 Code
        df_final_merge['ISO-alpha3 Code'] = df_final_merge['ISO-alpha3 Code'].fillna(df_final_merge.groupby('Country name')['ISO-alpha3 Code'].transform('first'))
        pays_ISO = {'Macedonia': 'MKD'}
        df_final_merge['ISO-alpha3 Code'] = df_final_merge['ISO-alpha3 Code'].fillna(df_final_merge['Country name'].map(pays_ISO))

        # Convert year to string for ID
        df_final_merge['year'] = df_final_merge['year'].astype('str')
        df_final_merge['id'] = df_final_merge['year'] + "-" + df_final_merge['ISO-alpha3 Code']

        # Load and merge GDP data
        GDP = pd.read_excel(FILE_PATH_GDP)
        GDP['Time'] = GDP['Time'].astype('str')
        GDP['id'] = GDP['Time'] + "-" + GDP['Country Code']
        GDP = GDP.rename(columns={'Time': 'year_gdp', 'Country Name': 'Country name_gdp', 'Country Code': 'ISO-alpha3 Code_gdp', 'LN': 'Logged GDP per capita_new'})
        GDP_merge = GDP[['id', 'year_gdp', 'Country name_gdp', 'ISO-alpha3 Code_gdp', 'Logged GDP per capita_new']]
        df_final_merge = pd.merge(df_final_merge, GDP_merge, on='id', how='left')
        df_final_merge['Logged GDP per capita'] = df_final_merge['Logged GDP per capita'].fillna(df_final_merge['Logged GDP per capita_new'])
        df_final_merge = df_final_merge.drop(columns=['Logged GDP per capita_new', 'year_gdp', 'Country name_gdp', 'ISO-alpha3 Code_gdp'])


        # Load and merge Life Expectancy data
        Life = pd.read_csv(FILE_PATH_LIFE, sep=';')
        Life['Period'] = Life['Period'].astype('str')
        Life['id'] = Life['Period'] + "-" + Life['SpatialDimValueCode']
        Life = Life.rename(columns={'Period': 'year_life', 'Location': 'Country name_life', 'SpatialDimValueCode': 'ISO-alpha3 Code_life', 'FactValueNumeric': 'Healthy life expectancy_new'})
        Life = Life.loc[(Life['Dim1'] == 'Both sexes')]
        Life_merge = Life[['id', 'year_life', 'Country name_life', 'ISO-alpha3 Code_life', 'Healthy life expectancy_new']]
        df_final_merge = pd.merge(df_final_merge, Life_merge, on='id', how='left')
        df_final_merge['Healthy life expectancy'] = df_final_merge['Healthy life expectancy'].fillna(df_final_merge['Healthy life expectancy_new'])
        df_final_merge = df_final_merge.drop(columns=['Healthy life expectancy_new', 'year_life', 'Country name_life', 'ISO-alpha3 Code_life'])

        # Drop rows that are entirely NaN in relevant columns (result of initial merge with empty ID years)
        colonnes_a_checker = ['Life Ladder', 'Logged GDP per capita', 'Social support', 'Healthy life expectancy',
                              'Freedom to make life choices', 'Generosity', 'Perceptions of corruption', 'Positive affect',
                              'Negative affect']
        df_final_merge['lignes_NaN'] = df_final_merge[colonnes_a_checker].isna().all(axis=1)
        index_to_drop = df_final_merge[df_final_merge['lignes_NaN'] == True].index
        df_final_merge = df_final_merge.drop(index_to_drop)
        df_final_merge = df_final_merge.drop(columns=['lignes_NaN'])

    return df_final_merge, df

# Charger les données (cette fonction ne s'exécutera qu'une seule fois grâce à @st.cache_data)
df_processed, df_original = load_and_preprocess_data()

# Mettre le DataFrame traité dans l'état de session pour qu'il soit accessible par toutes les "pages"
st.session_state['df_processed'] = df_processed
st.session_state['df_original'] = df_original


# Base df avec code ID & Pays
df = pd.read_csv(FILE_PATH_WHR, sep=',')
# Add 'id' column for merging
df['year'] = df['year'].astype('str')
df['id'] = df['year'] + "-" + df['Country name']
# Load ID base
ID = pd.read_csv(FILE_PATH_MERGE_ID, sep=';')
# Merge df & ID base
merge_df_ISO = ID.merge(df, on='id', how='outer')
merge_df_ISO = merge_df_ISO.drop(columns=['Country name_y', 'year_y'])
merge_df_ISO = merge_df_ISO.rename(columns={'year_x': 'year', 'Country name_x': 'Country name'})



# --- Fonctions pour chaque "page" ---

def home_page(): 

    st.title("🌍 Projet Analyse du bien-être sur Terre - Data Analyse - Feb25 Continu")

    st.markdown("---")

    st.image('STREAMLIT-Couv.jpg')


    st.markdown("---")
    st.subheader(" 🌟 Présentation du sujet, du problème et des enjeux")
    st.markdown(" ##### Dans ce projet nous allons effectuer une analyse approfondie des données collectées par le World Happiness Report mené par l’Organisation des Nations Unies.")
    
    st.markdown("""
    
    Cette enquête a pour objectif d’estimer le bonheur des pays autour de la planète et de comparer la qualité de vie des populations par nation et par zone géographique 
    en collectant de nombreuses données socio-économiques. Les données sur lesquelles travaille l’ONU intègrent différents aspects comme le PIB par habitant, le soutien social, 
    l'espérance de vie d’un individu en bonne santé depuis sa naissance, la liberté de faire des propres choix de vie, la générosité et la perception de la corruption, 
    mettant ainsi en lumière des disparités parfois significatives entre pays. 
                          
     """)
    
    st.info("######  L’objectif de ce projet est de présenter ces données à l’aide de visualisations interactives et de déterminer les combinaisons de facteurs permettant " \
    "d’expliquer pourquoi certains pays sont mieux classés que les autres.")
    
    st.markdown("### 🎯 Nos Questions Clés")  

    st.markdown("""          

    **- Quels sont les 10 pays les plus heureux ?** 
                
    **- Quels sont les 10 pays les moins heureux ?** 
                
    **- Les Etats les plus riches sont-ils considérés comme les plus heureux ?** 
                
    **- Quels sont les facteurs les plus déterminants du bonheur ?**
                
    **- Existe-t-il une fracture du bonheur entre zones géographiques ou entre continents ?** 
                
    **- Et surtout : comment ces facteurs interagissent-ils pour favoriser, ou au contraire freiner, le bien-être global d’une population ?**       
    
    """)


    st.info("###### C’est à travers une analyse structurée du bien-être sur Terre que nous tenterons d'apporter des éléments de réponse à ces questions.")

    
    


def presentation_donnees():
    st.title("🌍 Présentation des jeux de données du WHR")

    st.markdown("""
                
    Les fichiers “world-happiness-report-2021.csv” et “world-happiness-report.csv” regroupent les résultats du rapport sur le bonheur mené sous la direction de l’ONU. 
    
    Les principales données proviennent d’un sondage réalisé par l’entreprise Gallup. "
                
    """)
    st.subheader(" Voici un aperçu des premières lignes et des informations générales des dataset initiaux :")
    st.markdown("""
    
    **🌟 Chaque ligne des deux jeux de données représente un pays, une année et les scores de bien-être selon plusieurs critères établis.**
                
    """)

    st.markdown("---")
    st.subheader("1.1 WHR 2005-2020")
    st.write(f"Nombre de lignes dataframe 2005 à 2020 : **{len(WHR_2005_2020)}**")
    st.write(f"Nombre de colonnes : **{WHR_2005_2020.shape[1]}**")
    st.write(f"Nombre total de valeurs manquantes : **{WHR_2005_2020.isna().sum().sum()}**")
    st.dataframe(WHR_2005_2020.head())

    info_2005_2020 = WHR_2005_2020.info
    st.text(info_2005_2020)
    
    info_str = ""
    with redirect_stdout(sys.stdout) as stdout:
        WHR_2005_2020.info()
        info_str = stdout.getvalue()
    st.text(info_str)

    st.dataframe(WHR_2005_2020.describe())

    st.markdown("---")
    st.subheader("1.2 WHR 2021")
    st.write(f"Nombre de lignes dataframe 2021 : **{len(WHR_2021)}**")
    st.write(f"Nombre de colonnes : **{WHR_2021.shape[1]}**")
    st.write(f"Nombre total de valeurs manquantes : **{WHR_2021.isna().sum().sum()}**")
    st.dataframe(WHR_2021.head())
    


    st.dataframe(WHR_2021.describe())

def dataviz():
    st.title("🌍 Analyse des données du WHR avec figures de DataVizualization")

    st.subheader("1.1 Score du bonheur")

    st.markdown("""
    Les variables “Ladder score” et “Life Ladder” correspondent à l'indice de bonheur subjectif sur "l'échelle du Bonheur". 
                
    Selon l'étude, chaque pays a obtenu un score basé sur une échelle de 0 à 10 (le 0 représente le score le plus bas et le 10 le meilleur).
    
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("DATA 2005-2020 : Distribution Life Ladder")
        fig, ax = plt.subplots(figsize=(3, 3))
        ax.set_ylim(0, 10)
        sns.boxplot(y= WHR_2005_2020["Life Ladder"], color="blue")
        ax.set_ylabel("")
        st.pyplot(fig, use_container_width=False)

    with col2:
        st.subheader("DATA 2021 : Distribution Ladder Score")
        fig, ax = plt.subplots(figsize=(3, 3))
        ax.set_ylim(0, 10)
        sns.boxplot(y= WHR_2021["Ladder score"], color="blue")
        ax.set_ylabel("")
        st.pyplot(fig, use_container_width=False)

    st.subheader("1.2 PIB par habitant")

    st.markdown("""
    Les variables “Logged GDP per Capita” et “Log GDP per Capita” représentent le PIB par habitant. Ces variables sont “logarithmées” pour atténuer l’impact des valeurs extrêmes.
    
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("DATA 2005-2020 : Distribution Log GDP per capita")
        fig, ax = plt.subplots(figsize=(3, 3))
        sns.boxplot(y= WHR_2005_2020["Log GDP per capita"], color="#C832BE")
        ax.set_ylabel("")
        st.pyplot(fig, use_container_width=False)

    with col2:
        st.subheader("DATA 2021 : Distribution Logged GDP per capita")
        fig, ax = plt.subplots(figsize=(3, 3))
        sns.boxplot(y= WHR_2021["Logged GDP per capita"], color="#C832BE")
        ax.set_ylabel("")
        st.pyplot(fig, use_container_width=False)

    st.subheader("1.3 Support Social")

    st.markdown("""
    La variable Social support mesure la perception des citoyens d’avoir quelqu’un sur qui compter en cas de besoin.
    
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("DATA 2005-2020 : Distribution Social Support")
        fig, ax = plt.subplots(figsize=(3, 3))
        sns.boxplot(y= WHR_2005_2020["Social support"], color="#FF7873")
        ax.set_ylabel("")
        st.pyplot(fig, use_container_width=False)

    with col2:
        st.subheader("DATA 2021 : Distribution Social Support")
        fig, ax = plt.subplots(figsize=(3, 3))
        sns.boxplot(y= WHR_2021["Social support"], color="#FF7873")
        ax.set_ylabel("")
        st.pyplot(fig, use_container_width=False)

    st.subheader("1.4 Espérance de vie en bonne santé")

    st.markdown("""
    Les variables “Healthy life expectancy” et “Healthy life expectancy at birth” représentent l’espérance de vie ajustée sur la santé, 
    c’est-à-dire le nombre moyen d’années qu’un individu peut espérer vivre en bonne santé dans chaque pays.

    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("DATA 2005-2020 : Healthy life expectancy at birth")
        fig, ax = plt.subplots(figsize=(3, 3))
        sns.boxplot(y= WHR_2005_2020["Healthy life expectancy at birth"], color="#009692")
        ax.set_ylabel("")
        st.pyplot(fig, use_container_width=False)

    with col2:
        st.subheader("DATA 2021 : Healthy life expectancy")
        fig, ax = plt.subplots(figsize=(3, 3))
        sns.boxplot(y= WHR_2021["Healthy life expectancy"], color="#009692")
        ax.set_ylabel("")
        st.pyplot(fig, use_container_width=False)

    st.subheader("1.5 Liberté de faire des choix")

    st.markdown("""
    La variable “Freedom to make life choices” reflète la perception des individus quant à leur liberté de choisir leur mode de vie, leurs décisions personnelles et leur avenir. 
    
    Elle est mesurée sur une échelle de 0 à 1, où 1 représente un haut niveau de liberté perçue.

    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("DATA 2005-2020 : Freedom to make life choices")
        fig, ax = plt.subplots(figsize=(3, 3))
        sns.boxplot(y= WHR_2005_2020["Freedom to make life choices"], color="#FFA100")
        ax.set_ylabel("")
        st.pyplot(fig, use_container_width=False)

    with col2:
        st.subheader("DATA 2021 : Freedom to make life choices")
        fig, ax = plt.subplots(figsize=(3, 3))
        sns.boxplot(y= WHR_2021["Freedom to make life choices"], color="#FFA100")
        ax.set_ylabel("")
        st.pyplot(fig, use_container_width=False)

    st.subheader("1.6 Générosité")

    st.markdown("""
    La variable Generosity mesure la tendance des citoyens à faire des dons (en argent ou en temps) à des œuvres caritatives, rapportée à leur revenu. 

    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("DATA 2005-2020 : Generosity")
        fig, ax = plt.subplots(figsize=(3, 3))
        sns.boxplot(y= WHR_2005_2020["Generosity"], color="#7DB456")
        ax.set_ylabel("")
        st.pyplot(fig, use_container_width=False)

    with col2:
        st.subheader("DATA 2021 : Generosity")
        fig, ax = plt.subplots(figsize=(3, 3))
        sns.boxplot(y= WHR_2021["Generosity"], color="#7DB456")
        ax.set_ylabel("")
        st.pyplot(fig, use_container_width=False)

    st.subheader("1.7 Perception de la corruption")

    st.markdown("""
    La variable Perceptions of corruption mesure le niveau de corruption perçue par les citoyens d’un pays dans les institutions publiques (gouvernement, entreprises). 
    
    Elle est exprimée sur une échelle de 0 à 1 (0 = corruption perçue comme très forte et 1 = très faible corruption perçue)

    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("DATA 2005-2020 : Perceptions of corruption")
        fig, ax = plt.subplots(figsize=(3, 3))
        sns.boxplot(y= WHR_2005_2020["Perceptions of corruption"], color="#C3175C")
        ax.set_ylabel("")
        st.pyplot(fig, use_container_width=False)

    with col2:
        st.subheader("DATA 2021 : Perceptions of corruption")
        fig, ax = plt.subplots(figsize=(3, 3))
        sns.boxplot(y= WHR_2021["Perceptions of corruption"], color="#C3175C")
        ax.set_ylabel("")
        st.pyplot(fig, use_container_width=False)
  


def pre_processing():
    st.title("🌍 Pré Processing et nettoyage des données")
    
    st.markdown(""" #####
    La base de données de 2005 à 2020 ne comporte pas énormément de valeurs manquantes (373 NaN). 
    
    Toutefois, en approfondissant l’analyse, en fusionnant le dataframe avec une base continue: Id -> Année & pays de 2005 à 2020. Ajout du code ISO alpha 3: code universel par pays.
    
    Le constat n'est plus le même : il manque un grand nombre de données par année et par pays.

    """)

    st.subheader("🎯 Poursuivons notre analyse afin d'enrichir le dataset sur les valeurs manquantes, en voici les différentes étapes :")

    st.markdown("""
                
    - Enrichir l'année 2020 avec le rapport du WHR disponible en ligne
    - Fusion de notre 2ème jeu de données du WHR sur l'année 2021
    - Enrichir les données de l'indicateur du PIB avec les données de la Banque Mondiale
    - Enrichir les données de l'indicateur de l'espérance de vie avec les données de l'OMS.

    """)

    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("1.1 Données Originales")
        st.write(f"Nombre de lignes dataframe 2005-2020 : **{len(df_original)}**")
        st.write(f"Nombre de colonnes : **{df_original.shape[1]}**")
        st.write(f"Nombre total de valeurs manquantes originales : **{df_original.isna().sum().sum()}**")
        total_nan_original = df_original.isna().sum().sum()
        st.write(f"Pourcentage de valeurs manquantes originales : **{round((total_nan_original / (WHR_2005_2020.shape[0] * WHR_2005_2020.shape[1])) * 100, 2)}%**")
        st.dataframe(df_original.isna().sum().rename("NaN Count").reset_index().rename(columns={'index': 'Column'}))
    
    with col2:
        st.subheader("1.2 Données avec code ID & Pays")
        st.write(f"Nombre de lignes dataframe 2005-2020 : **{len(merge_df_ISO)}**")
        st.write(f"Nombre de colonnes : **{merge_df_ISO.shape[1]}**")
        st.write(f"Nombre total de valeurs manquantes originales : **{merge_df_ISO.isna().sum().sum()}**")
        total_nan_merge = merge_df_ISO.isna().sum().sum()
        st.write(f"Pourcentage de valeurs manquantes originales : **{round((total_nan_merge / (merge_df_ISO.shape[0] * merge_df_ISO.shape[1])) * 100, 2)}%**")
        st.dataframe(merge_df_ISO.isna().sum().rename("NaN Count").reset_index().rename(columns={'index': 'Column'}))

    with col3:
        st.subheader("1.3 Données Prétraitées et Enrichies")
        st.write(f"Nombre de lignes après traitement : **{df_processed.shape[0]}**")
        st.write(f"Nombre de colonnes après traitement : **{df_processed.shape[1]}**")
        total_nan_processed = df_processed.isna().sum().sum()
        st.write(f"Nombre total de valeurs manquantes après traitement : **{total_nan_processed}**")
        st.write(f"Pourcentage de valeurs manquantes après traitement : **{round((total_nan_processed / (df_processed.shape[0] * df_processed.shape[1])) * 100, 2)}%**")
        st.dataframe(df_processed.isna().sum().rename("NaN Count").reset_index().rename(columns={'index': 'Column'}))

    st.markdown("---")
    st.subheader("1.4 Aperçu de notre dataset final")

    st.write("Le dataset a été fusionné avec des données supplémentaires et les valeurs manquantes ont été traitées. En voici les premières lignes :")

    st.dataframe(df_processed.head(10))

    st.markdown("---")
    st.markdown("""
    Il nous reste encore 5149 données manquantes, soit 13% de valeurs manquantes dans notre jeu de données. 
    Nous nous rendons compte que notre analyse ne va pas être si aisée au vu du grand nombre de données absentes.
    
    Nous avons fait le choix de ne pas dénaturer l’analyse du WHR et de ne pas remplacer les valeurs manquantes par des moyennes ou des données externes.
    En effet, l’analyse du WHR est bien spécifique avec des questions posées sur un échantillon de personnes. 
                
    Nous allons donc poursuivre notre analyse avec, tout de même, un grand nombre de données exploitables sur un large panel de 167 pays 
    et avec une amplitude temporelle de 17 années (2005 à 2021).
    

    """)
    st.markdown("---")
    st.info("#### 🌟 Le dataset est maintenant prêt pour une analyse approfondie.")

def analyse_des_tendances_page():
    st.title("🌍 Tendances Globales (2005-2021)")
    st.markdown("---")
    st.write("Explorons comment les indicateurs clés du bonheur ont évolué au fil des ans.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Bonheur Global (Life Ladder)")
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(x='year', y='Life Ladder', data=df_processed, ax=ax, palette='viridis')
        ax.set_ylim(3, 7)
        ax.set_title("Évolution du Life Ladder")
        ax.set_xlabel("Année")
        ax.set_ylabel("Score Life Ladder")
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

    with col2:
        st.subheader("Espérance de Vie en Bonne Santé")
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(x='year', y='Healthy life expectancy', data=df_processed, ax=ax, palette='mako')
        ax.set_ylim(45, 70)
        ax.set_title("Évolution de l'Espérance de Vie")
        ax.set_xlabel("Année")
        ax.set_ylabel("Années")
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

    with col3:
        st.subheader("PIB par Habitant")
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(x='year', y='Logged GDP per capita', data=df_processed, ax=ax, palette='rocket')
        ax.set_ylim(7, 10)
        ax.set_title("Évolution du Logged GDP per capita")
        ax.set_xlabel("Année")
        ax.set_ylabel("Log PIB par Habitant")
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

    st.markdown("---")
    st.markdown("""
    L'année 2005 contient seulement 27 données sur les 167 pays présents, ce qui explique cet écart.
    
    Il faudra pousser l’analyse en détail par indicateurs afin de comprendre ces différentes évolutions du “life ladder” au fil des années. 
    Ici, on représente seulement une moyenne de l’ensemble des pays par année. 
    
    Attention toutefois, toutes les années ne disposent pas du même nombre de pays par année.
                
    """)

    st.info("##### Les graphiques montrent une tendance générale à l'amélioration de l'espérance de vie et du PIB, tandis que le score du bonheur reste relativement stable avec des variations annuelles.")


def correlations():
    st.title("🌍 Matrice de corrélation")
    st.markdown("---")

    st.write("##### La matrice ci-dessous montre la corrélation entre les différents indicateurs du World Happiness Report.")
    cor = df_processed.corr(numeric_only=True)
    fig_corr, ax_corr = plt.subplots(figsize=(10, 8))
    sns.heatmap(cor, annot=True, ax=ax_corr, cmap='coolwarm', fmt=".2f")
    ax_corr.set_title("Matrice de Corrélation WHR (2005-2021)")
    st.pyplot(fig_corr)

    st.markdown("""#####
    Les indicateurs comme le PIB par habitant, l’espérance de vie en bonne santé, le support social ont l’air d’être fortement corrélés au score du bonheur. 
    D’autres indicateurs comme la corruption ou la générosité ont quant à eux, au contraire, une très faible corrélation. 
    Attention, toutefois il s’agit des indicateurs avec le plus de données manquantes.
    """)

    st.markdown("---")

 
    st.info("#### 🌟 A présent poursuivons notre analyse du bien-être sur terre avec l'outil PowerBI. Nous étofferons notre analyse avec des indicateurs externes.")


# --- Logiciel de navigation (dans la barre latérale) ---
st.sidebar.title("Analyse du bien-être")
page_selection = st.sidebar.radio(
    "Choisissez une page :",
    (
        "Accueil",
        "Synthèse jeux de données",
        "Datavisualisation",
        "Pré Processing des données",
        "Analyse des Tendances",
        "Matrice de corrélation"
    )
)

# --- Affichage de la page sélectionnée ---
if page_selection == "Accueil":
    home_page()
elif page_selection == "Synthèse jeux de données":
    presentation_donnees()  
elif page_selection == "Datavisualisation":
    dataviz()  
elif page_selection == "Pré Processing des données":
    pre_processing()
elif page_selection == "Analyse des Tendances":
    analyse_des_tendances_page()
elif page_selection == "Matrice de corrélation":

    correlations()



