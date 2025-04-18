import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from target_analyzer import TargetAnalyzer

data_sources = ["ot_genetics_portal", "gene_burden", "eva", "genomics_england", "gene2phenotype",
                "uniprot_literature", "uniprot_variants", "orphanet", "clingen", "cancer_gene_census",
                "intogen", "eva_somatic", "cancer_biomarkers", "chembl", "crispr_screen", "crispr",
                "slapenrich", "progeny", "reactome", "sysbio", "europepmc", "expression_atlas",
                "impc", "ot_crispr_validation", "ot_crispr", "encore"]

def get_disease_descendants(disease):
    analyzer = TargetAnalyzer(disease)
    descendants = analyzer.get_descendants(disease)
    return descendants

def home():
    with st.container():
        st.header("Enter Target and Select Diseases")
        target = st.text_input("Enter the target:")
        if target:
            disease_options = ["immune system disease", 
                               "hematological measurement", "inflammatory biomarker measurement","inflammatory disease"]
            selected_diseases = st.multiselect("Select Diseases:", disease_options)
            if selected_diseases and st.button("Next ->"):
                st.session_state['target'] = target
                st.session_state['selected_diseases'] = selected_diseases
                st.session_state['descendants'] = {d: get_disease_descendants(d) for d in selected_diseases}
                st.session_state['page_name'] = 'descendants'

def operations():
    with st.container():
        st.header("Task Dashboard")

        if st.session_state.get('selected_diseases'):
            st.subheader("Selected Diseases:")
            st.write(', '.join(st.session_state['selected_diseases']))

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Calculate Association"):
                    st.session_state['page_name'] = 'calculate_association'
            with col2:
                if st.button("Rank Targets"):
                    st.session_state['page_name'] = 'rank_targets'

            if st.button("Back to Home"):
                st.session_state['page_name'] = 'home'

        else:
            st.warning("No diseases selected. Please go back to the Home page and select diseases.")
            if st.button("Back to Home"):
                st.session_state['page_name'] = 'home'

def filter_associated_diseases(api_response, descendants):
    associated_diseases = api_response['data']['target']['associatedDiseases']['rows']
    descendant_ids = {disease_id for sublist in descendants.values() for disease_id in sublist}
    filtered_associations = [disease for disease in associated_diseases if disease['disease']['id'] in descendant_ids]
    return filtered_associations

def create_disease_dataframe(diseases):
    rows = []
    for disease in diseases:
        row = {'disease_name': disease['disease']['name'], 'aggregated_score': disease['score']}
        for source in data_sources:
            row[source] = 0.0
        for ds_score in disease['datasourceScores']:
            if ds_score['componentId'] in data_sources:
                row[ds_score['componentId']] = ds_score['score']
        rows.append(row)
    df = pd.DataFrame(rows)
    cols = ['disease_name', 'aggregated_score'] + [ds for ds in data_sources if ds in df.columns]
    return df[cols]

def calculate_association_page():
    with st.container():
        st.header("Calculate Association for Selected Diseases")
        response = TargetAnalyzer(st.session_state['target']).get_associated_diseases()
        if 'descendants' in st.session_state and st.session_state['descendants']:
            descendants_ids = {id for ids in st.session_state['descendants'].values() for id in ids}
            for disease_id in descendants_ids:
                filtered_associations = filter_associated_diseases(response, {disease_id: st.session_state['descendants'][disease_id]})
                
                if filtered_associations:
                    st.subheader(f"Associations for {filtered_associations[0]['disease']['name']}")
                    df = create_disease_dataframe(filtered_associations)
                    st.dataframe(df)                    
                    # Plotting the association scores for this particular disease
                    df.set_index('disease_name', inplace=True)
                    df = df.loc[:, (df != 0).any(axis=0)]  # Removing zero columns
                    data = df.select_dtypes(include=['float64', 'int64'])
                    if not data.empty:
                        plt.figure(figsize=(10, 8))
                        sns.heatmap(data, annot=True, cmap="coolwarm", fmt=".2f")
                        plt.title(f"Association Scores for {df.index[0]}")
                        plt.xlabel("Data Sources")
                        plt.ylabel("Disease")
                        fig = plt.gcf() 
                        st.pyplot(fig)
                    else:
                        st.warning(f"All data source scores are zero for {filtered_associations[0]['disease']['name']}.")
                else:
                    st.warning(f"No associated diseases found in the descendants for ID: {disease_id}.")
        else:
            st.error("No descendants data available. Please ensure diseases are selected and descendants are fetched.")

        st.button("Back", on_click=lambda: st.session_state.update({'page_name': 'descendants'}))


def rank_targets_page():
    with st.container():
        st.header("Rank of Targets Across Diseases")
        if 'selected_diseases' in st.session_state and st.session_state['selected_diseases']:
            all_rankings = []
            for parent_disease in st.session_state['selected_diseases']:
                df = TargetAnalyzer(st.session_state['target']).rank_my_target(parent_disease=parent_disease)
                if isinstance(df, pd.DataFrame):
                    df['Parent Disease'] = parent_disease
                    all_rankings.append(df)
                else:
                    st.error(f"No valid ranks found for {parent_disease}: {df}")
            if all_rankings:
                combined_df = pd.concat(all_rankings).reset_index(drop=True)
                columns_order = ['Parent Disease', 'Gene', 'Disease', 'Rank']
                combined_df = combined_df[columns_order]
                st.dataframe(combined_df)
            else:
                st.write("No diseases found where the target has a rank of 500 or less across all selected diseases.")
        else:
            st.error("No diseases selected. Please go back to the Home page and select diseases.")

        st.button("Back", on_click=lambda: st.session_state.update({'page_name': 'descendants'}))


def main():
    st.title("Target Dossier")

    if 'page_name' not in st.session_state:
        st.session_state['page_name'] = 'home'
    
    if st.session_state['page_name'] == 'home':
        home()
    elif st.session_state['page_name'] == 'descendants':
        operations()
    elif st.session_state['page_name'] == 'calculate_association':
        calculate_association_page()
    elif st.session_state['page_name'] == 'rank_targets':
        rank_targets_page()

if __name__ == "__main__":
    main()
