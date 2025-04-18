import ipywidgets as widgets
from ipywidgets import interact, VBox, Dropdown, Output
from IPython.display import display, clear_output, HTML, IFrame, Markdown
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.colors import Normalize
from matplotlib.cm import viridis
import seaborn as sns
import json
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from target_analyzer import TargetAnalyzer

data_source_groups = {
    "Association Score": ["Overall Association score"],
    "Genetic Association": ["ot_genetics_portal", "gene_burden", "eva", "genomics_england", "gene2phenotype", "uniprot_literature", "uniprot_variants", "orphanet", "clingen"],
    "Somatic Mutations": ["cancer_gene_census", "intogen", "eva_somatic", "cancer_biomarkers"],
    "Known Drug": ["chembl"],
    "Affected Pathway": ["crispr_screen", "crispr", "slapenrich", "progeny", "reactome", "sysbio"],
    "Literature": ["europepmc"],
    "RNA Expression": ["expression_atlas"],
    "Animal Model": ["impc"]
}

def display_target_information(api_response: dict):
    target_info = api_response['data']['target']
    display(widgets.HTML(f"<b>Target ID:</b> {target_info['id']}<br>", layout=widgets.Layout(margin='10px 0px')))
    
    display(widgets.HTML("<b>Function Descriptions:</b>", layout=widgets.Layout(margin='10px 0px')))
    for description in target_info['functionDescriptions']:
        display(widgets.HTML(f"<span style='font-size: 14px;'>- {description}</span><br>", layout=widgets.Layout(margin='5px 0px')))
    
    synonyms_df = pd.DataFrame(target_info['synonyms'])
    uniprot_synonyms = synonyms_df[synonyms_df['source'] == 'uniprot']['label'].tolist()
    
    if uniprot_synonyms:
        display(widgets.HTML("<b>Synonyms (from UniProt):</b>", layout=widgets.Layout(margin='10px 0px')))
        for synonym in uniprot_synonyms:
            display(widgets.HTML(f"<span style='font-size: 14px;'>- {synonym}</span><br>", layout=widgets.Layout(margin='5px 0px')))
    else:
        if not synonyms_df.empty:
            any_synonyms = synonyms_df.iloc[0]['label']
            display(widgets.HTML(f"<b>Synonyms from {synonyms_df.iloc[0]['source']}:</b>", layout=widgets.Layout(margin='10px 0px')))
            display(widgets.HTML(f"<span style='font-size: 14px;'>- {any_synonyms}</span><br>", layout=widgets.Layout(margin='5px 0px')))
        else:
            display(widgets.HTML("<i>No synonyms found.</i>", layout=widgets.Layout(margin='10px 0px')))


def get_disease_descendants(disease):
    analyzer = TargetAnalyzer(disease)
    descendants = analyzer.get_descendants(disease)
    return descendants

def select_diseases(target, disease_options):
    @interact(selected_diseases=widgets.SelectMultiple(options=disease_options, description="Select Diseases"))
    def get_selected_diseases(selected_diseases):
        if selected_diseases:
            descendants = {d: get_disease_descendants(d) for d in selected_diseases}
            calculate_association(target, selected_diseases, descendants)

def filter_associated_diseases(api_response, disease_ids):
    associated_diseases = api_response['data']['target']['associatedDiseases']['rows']
    return [disease for disease in associated_diseases if disease['disease']['id'] in disease_ids]

def create_disease_dataframe(diseases):
    """Create a DataFrame from disease data with scores from various sources."""
    rows = []
    all_data_sources = [ds for group in data_source_groups.values() for ds in group if ds != 'Overall Association score']
    for disease in diseases:
        row = {
            'disease_name': disease['disease']['name'], 
            'Overall Association score': disease['score']
        }

        for source in all_data_sources:
            row[source] = 0.0
        for ds_score in disease.get('datasourceScores', []):
            if ds_score['componentId'] in all_data_sources:
                row[ds_score['componentId']] = ds_score['score']
        rows.append(row)

    df = pd.DataFrame(rows)

    return df

def plot_disease_associations(df, group):
    """Plot the disease associations using Plotly with dynamic sizing."""
    group_sources = data_source_groups.get(group, [])
    data = df[['disease_name'] + group_sources].set_index('disease_name')

    # Calculate dynamic plot dimensions
    min_height = 600
    min_width = 800
    plot_height = max(min_height, len(data.index) * 25)
    plot_width = max(min_width, len(group_sources) * 120)

    fig = go.Figure(data=go.Heatmap(
        z=data.values,
        x=data.columns,
        y=data.index,
        colorscale='Blues',
        colorbar=dict(title='Score'),
        zmin=0,
        zmax=1
    ))

    fig.update_layout(
        title=f'Disease Associations for {group}',
        xaxis_title='Data Sources',
        yaxis_title='Disease',
        xaxis=dict(tickangle=-45, tickmode='array', tickvals=list(range(len(data.columns))), ticktext=data.columns.tolist()),
        yaxis=dict(tickmode='array', tickvals=list(range(len(data.index))), ticktext=data.index.tolist()),
        autosize=False,
        width=plot_width,
        height=plot_height
    )

    fig.show()

# def plot_disease_associations(df, group):
#     """Plot the disease associations for the selected data source group."""
#     group_sources = data_source_groups.get(group, [])
#     data = df[['disease_name'] + group_sources].set_index('disease_name')
#     plt.figure(figsize=(14, max(5, len(data) * 0.5)))
#     sns.heatmap(data, annot=True, cmap="Blues", fmt=".3f", cbar=True, vmin=0, vmax=1)
#     plt.title(f'Disease Associations for {group}')
#     plt.xlabel('Data Sources')
#     plt.ylabel('Disease')
#     plt.show()

def calculate_association(target, selected_diseases, descendants):
    """Calculate association scores and display results with proper scope handling."""
    response = TargetAnalyzer(target).get_associated_diseases()
    results = {}
    
    def plot_for_disease(disease, df):
        print(f"Disease: {disease}")
        display(df)

        group_dropdown = Dropdown(options=list(data_source_groups.keys()), description="Data Group:", value="Association Score")
        out = Output() 
        def on_group_change(change):
            if change['new']:
                with out:
                    clear_output(wait=True)
                    plot_disease_associations(df, change['new'])
                    clear_output(wait=True)

        group_dropdown.observe(on_group_change, names='value')
        display(group_dropdown, out)
        on_group_change({'new': group_dropdown.value})
    
    for disease, ids in descendants.items():
        filtered_associations = filter_associated_diseases(response, set(ids))
        if filtered_associations:
            df = create_disease_dataframe(filtered_associations)
            if not df.empty:
                plot_for_disease(disease, df)
            else:
                print("All data source scores are zero for this disease.")
        else:
            print(f"No associated diseases found in the descendants for Disease: {disease}.")
        results[disease] = df
    
    return results

def setup_disease_selection_interface(default_target):
    disease_options = [
        "immune system disease", "hematological measurement",
        "inflammatory biomarker measurement", "measurements", "hematologic disease"
    ]

    checkboxes = [widgets.Checkbox(value=True, description=label) for label in disease_options]
    checkbox_container = VBox(children=checkboxes)

    target_input = widgets.Text(value=default_target, description="Enter Target:")

    select_button = widgets.Button(description="Select Diseases and Calculate")

    output_space = Output()
    
    def on_button_clicked(b):
        with output_space:
            clear_output(wait=True) 
            selected_diseases = [checkbox.description for checkbox in checkboxes if checkbox.value]
            target = target_input.value.strip()
            if target and selected_diseases:
                descendants = {d: get_disease_descendants(d) for d in selected_diseases}
                result = calculate_association(target, selected_diseases, descendants)
                print(result) 
            else:
                print("Please enter a target and select at least one disease.")
    
    select_button.on_click(on_button_clicked)

    ui = VBox([target_input, checkbox_container, select_button, output_space])
    display(ui)


def parse_and_plot_targetability(response, exact_target):
    key_to_column = {
        "maxClinicalTrialPhase": "Target in clinic",
        "isInMembrane": "Membrane protein",
        "isSecreted": "Secreted protein",
        "hasLigand": "Ligand binder",
        "hasSmallMoleculeBinder": "Small molecule binder",
        "hasPocket": "Predicted pockets",
        "mouseOrthologMaxIdentityPercentage": "Mouse ortholog identity",
        "hasHighQualityChemicalProbes": "Chemical probes",
        "geneticConstraint": "Genetic constraint",
        "mouseKOScore": "Mouse models",
        "geneEssentiality": "Gene essentiality",
        "hasSafetyEvent": "Known safety events",
        "isCancerDriverGene": "Cancer driver gene",
        "paralogMaxIdentityPercentage": "Paralogues",
        "tissueSpecificity": "Tissue specificity",
        "tissueDistribution": "Tissue distribution"
    }
    
    targets = response['data']['disease']['associatedTargets']
    
    if targets['count'] == 0:
        print("No data for targetability found for the given target.")
        return
    
    data = []
    symbols = []
    all_keys = list(key_to_column.values())
    
    for target_info in targets['rows']:
        target = target_info['target']
        if target['approvedSymbol'] == exact_target:
            symbols.append(target['approvedSymbol'])
            prioritisation_items = {item['key']: float(item['value']) for item in target['prioritisation']['items']}
            row = [prioritisation_items.get(key, np.nan) for key in key_to_column.keys()]
            data.append(row)
    
    if not symbols:
        print(f"No exact match found for target '{exact_target}'.")
        return
    
    heatmap_data = pd.DataFrame(data, columns=all_keys, index=symbols).fillna(np.nan)
    
    plt.figure(figsize=(14, 4))
    cmap = "viridis"
    norm = Normalize(vmin=-1, vmax=1)
    heatmap = sns.heatmap(heatmap_data, annot=True, cmap=cmap, cbar_kws={'label': 'Value'}, linewidths=.5)
    plt.title('Target Prioritisation Heatmap')
    plt.xlabel('Prioritisation Features')
    plt.ylabel('Approved Symbol')
    
    cmap = plt.get_cmap(cmap)
    favourable_color = cmap(norm(1))
    unfavourable_color = cmap(norm(-1))
    no_data_color = 'white'
    
    legend_elements = [
        Patch(facecolor=favourable_color, edgecolor='black', label='1: Favourable'),
        Patch(facecolor=unfavourable_color, edgecolor='black', label='-1: Unfavourable'),
        Patch(facecolor=no_data_color, edgecolor='black', label='No evidence')
    ]
    plt.legend(handles=legend_elements, loc='lower right', bbox_to_anchor=(1.15, 1.0))
    
    plt.show()


def plot_tractability(api_response):
    """
    Plot tractability data for each modality, ensuring the legend is placed outside the plot area without overlapping.
    """
    data = api_response['data']['target']['tractability']
    modalities_description = {
        'SM': 'Small molecule',
        'AB': 'Antibody',
        'PR': 'PROTAC',
        'OC': 'Other modalities'
    }
    organized_data = {mod: [] for mod in modalities_description.keys()}
    for item in data:
        organized_data[item['modality']].append(item)

    fig, axes = plt.subplots(nrows=1, ncols=len(organized_data), figsize=(15, 6),  
                             gridspec_kw={'width_ratios': [len(organized_data[mod]) for mod in organized_data]})

    available_patch = plt.Rectangle((0, 0), 1, 1, color='#90EE90')
    unavailable_patch = plt.Rectangle((0, 0), 1, 1, color='pink')

    for ax, (mod, items) in zip(axes, organized_data.items()):
        labels = [item['label'] for item in items]
        values = [item['value'] for item in items]
        colors = ['#90EE90' if val else 'pink' for val in values]
        bars = ax.barh(labels, [1] * len(labels), color=colors)
        ax.set_title(modalities_description[mod], fontweight='bold')
        ax.set_xlim(0, 1)
        ax.set_yticks([])
        ax.set_xlabel('Tractability')
        for i, label in enumerate(labels):
            ax.text(0.5, i, label, ha='center', va='center', color='black', fontsize=12)

    fig.subplots_adjust(right=0.8)
    plt.legend([available_patch, unavailable_patch], ['Available', 'Unavailable'],
               loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)

    plt.tight_layout()
    plt.show()


def parse_gene_ontology(api_response: dict):
    aspect_mapping = {'F': 'Molecular Function', 'P': 'Biological Process', 'C': 'Cellular Component'}
    aspect_order = ['Biological Process', 'Cellular Component', 'Molecular Function']
    
    ontology_list = []
    for entry in api_response['data']['target']['geneOntology']:
        term_link = f'<a href="https://amigo.geneontology.org/amigo/term/{entry["term"]["id"]}">{entry["term"]["name"]}</a>'
        aspect = aspect_mapping.get(entry['aspect'], entry['aspect'])
        ontology_list.append({
            'GO ID': entry['term']['id'],
            'Name': term_link,
            'Aspect': aspect,
            'Evidence': entry['evidence'],
            'Gene Product': entry['geneProduct'],
            'Source': entry['source']
        })
    
    df = pd.DataFrame(ontology_list)
    df['Aspect'] = pd.Categorical(df['Aspect'], categories=aspect_order, ordered=True)
    df.sort_values(by='Aspect', inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.index = df.index + 1
    
    return df


def display_go_ribbon(genes, file_name="go_ribbon1.html", width="100%", height="400px"):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <script type="module" src="https://unpkg.com/@geneontology/wc-go-ribbon/dist/wc-go-ribbon/wc-go-ribbon.esm.js"></script>
      <script nomodule="" src="https://unpkg.com/@geneontology/wc-go-ribbon/dist/wc-go-ribbon/wc-go-ribbon.js"></script>
    </head>
    <body>
      <!-- This adds the full go ribbon (strips + table) to your page for the specified genes -->
      <wc-go-ribbon subjects="{genes}"></wc-go-ribbon>
    </body>
    </html>
    """

    with open(file_name, "w") as file:
        file.write(html_content)

    display(IFrame(src=file_name, width=width, height=height))


def parse_mouse_phenotypes(response):
    data = response.get('data', {}).get('target', {}).get('mousePhenotypes', [])
    records = []
    for phenotype in data:
        gene_link = f'<a href="https://www.informatics.jax.org/marker/{phenotype["targetInModelMgiId"]}"> {phenotype["targetInModel"]}</a>'
        phenotype_link = f'<a href="https://www.ebi.ac.uk/ols4/ontologies/mp/terms?obo_id={phenotype["modelPhenotypeId"]}">{phenotype["modelPhenotypeLabel"]}</a>'
        category_links = ', '.join(
            [f'<a href="https://www.ebi.ac.uk/ols4/ontologies/mp/classes?obo_id={cls["id"]}">{cls["label"]}</a>' for cls in phenotype['modelPhenotypeClasses']]
        )
        
        allelic_composition_links = ', '.join(
            [f'<a href="https://www.informatics.jax.org/allele/genoview/{model["id"]}">{model["allelicComposition"]}</a>' for model in phenotype['biologicalModels']]
        )
        
        records.append({
            'Gene': gene_link,
            'Phenotype': phenotype_link,
            'Category': category_links,
            'Allelic Composition': allelic_composition_links})

    html_table = "<table><tr><th>Gene</th><th>Phenotype</th><th>Category</th><th>Allelic Composition</th></tr>"
    for record in records:
        html_table += "<tr>"
        for key, value in record.items():
            html_table += f"<td>{value}</td>"
        html_table += "</tr>"
    html_table += "</table>"
    
    return HTML(html_table)


def parse_and_display_homologue_table(api_response):
    homologues = api_response['data']['target']['homologues']
    data = {
        "Species": [],
        "Homology type": [],
        "Homologue": [],
        "Query %id": [],
        "Target %id": []
    }
    for homologue in homologues:
        data["Species"].append(homologue['speciesName'])
        data["Homology type"].append(homologue['homologyType'])
        
        link = f"https://identifiers.org/ensembl:{homologue['targetGeneId']}"
        data["Homologue"].append(f'<a href="{link}" target="_blank">{homologue["targetGeneSymbol"]}</a>')
        data["Query %id"].append(homologue['queryPercentageIdentity'])
        data["Target %id"].append(homologue['targetPercentageIdentity'])

    df = pd.DataFrame(data)
    html_style = """
    <style>
        table.dataframe { 
            font-size: 14px; 
        }
        table.dataframe th, table.dataframe td { 
            text-align: left; 
            padding: 10px;
        }
        table.dataframe th {
            background-color: #f4f4f4;
            color: #333;
        }
        a { 
            color: #337ab7; 
            text-decoration: none; 
        }
    </style>
    """
    
    html = html_style + df.to_html(escape=False, index=False)
    display(HTML(html))

def display_paralogs(results):
    species_codes = {
    "human": "9606",
    "mouse": "10090",
    "worm": "6239",
    "zebrafish": "7955"
    }
    columns = [
        "Species", "species_id", "Gene1 Symbol", "Paralog Score", "DIOPT Score", "Paralog Pair",
        "Gene2 Symbol", "1-Protein Acc", "2-Protein Acc", "Alignment Length", "Identity Score",
        "Similarity Score", "Common GO slim", "Common Yeast Paralogs", "Common Fly Paralogs",
        "Common Protein Interactors", "Common Genetic Interactors"
    ]

    data_rows = []
    for species, content in results.items():
        for item in content['data']:
            paralog_pair_url = f"https://www.flyrnai.org/tools/paralogs/web/expression/{item['Paralog_PairID']}"
            paralog_pair_link = f"<a href='{paralog_pair_url}'>text show expression data</a>"
            row = [
                species, species_codes[species], item['gene1'], item['Paralog_Score'], item['DIOPT_score'],
                paralog_pair_link, item['gene2'], item['protein1_acc'], item['protein2_acc'],
                item['alignment_length'], item['percent_id'], item['percent_similarity'],
                item['common_go_slim'], item['common_sc_orthologs'], item['common_dm_orthologs'],
                item['common_ppi_count'], item['common_gi_count']
            ]
            if species == 'human':
                row.extend([
                    item.get('coexpressed', '-'), item.get('tissue_correlation', '-'),
                    item.get('cell_line_correlation', '-')
                ])
                if 'Coexpressed Samples' not in columns:
                    columns.extend(["Coexpressed Samples", "Tissue Expression Correlation", "Cell Line Expression Correlation"])

            data_rows.append(row)
    df = pd.DataFrame(data_rows, columns=columns)

    # Sorting and resetting index for each species and sorting by Paralog Score
    df['Paralog Score'] = pd.to_numeric(df['Paralog Score'])
    df = df.sort_values(by=['Species', 'Paralog Score'], ascending=[True, False])
    df = df.groupby('Species').apply(lambda x: x.reset_index(drop=True)).reset_index(drop=True)
    df.index += 1

    display(HTML(df.to_html(escape=False)))

def prepare_data(expressions):
    """
    Prepare data from a structured dictionary into a pandas DataFrame.
    """
    data = []
    for exp in expressions:
        for organ in exp['tissue']['organs']:
            rna_score = max(0, exp['rna']['level'])
            protein_level = max(0, exp['protein']['level'])
            data.append({
                'Organ': organ,
                'Tissue': exp['tissue']['label'],
                'RNA Z-Score': rna_score,
                'Protein Level': protein_level
            })
    return pd.DataFrame(data)

def plot_organ_data(df, organ='All', output_widget=None):
    """
    Plot data based on the organ selected with interactive hover features.
    """
    if output_widget:
        output_widget.clear_output(wait=True)

    fig = make_subplots(rows=1, cols=2, subplot_titles=('RNA Z-Score', 'Protein Level'))
    
    if organ == 'All':
        max_rna = df.groupby('Organ')['RNA Z-Score'].max()
        max_protein = df.groupby('Organ')['Protein Level'].max()
        
        fig.add_trace(go.Bar(x=max_rna.index, y=max_rna, name='RNA Z-Score', marker_color='skyblue'), row=1, col=1)
        fig.add_trace(go.Bar(x=max_protein.index, y=max_protein, name='Protein Level', marker_color='salmon'), row=1, col=2)
        
    else:
        organ_data = df[df['Organ'] == organ]
        fig.add_trace(go.Bar(x=organ_data['Tissue'], y=organ_data['RNA Z-Score'], name='RNA Z-Score', marker_color='skyblue'), row=1, col=1)
        fig.add_trace(go.Bar(x=organ_data['Tissue'], y=organ_data['Protein Level'], name='Protein Level', marker_color='salmon'), row=1, col=2)
    

    fig.update_layout(
        title_text=f'RNA and Protein Levels {"by Organ" if organ == "All" else f"in {organ}"}',
        showlegend=False,
        height=400, 
        width=800   
    )

    if output_widget:
        with output_widget:
            fig.show()
    else:
        fig.show()



def setup_interactive_plot(df):
    """
    Set up and display interactive plot controls.
    """
    output_widget = widgets.Output()
    organs = ['All'] + sorted(df['Organ'].unique().tolist())
    organ_dropdown = widgets.Dropdown(
        options=organs,
        value='All',
        description='Organ:',
        disabled=False,
    )

    def on_dropdown_change(change):
        if change['type'] == 'change' and change['name'] == 'value':
            plot_organ_data(df, organ=change['new'], output_widget=output_widget)

    organ_dropdown.observe(on_dropdown_change)
    display(organ_dropdown, output_widget)
    plot_organ_data(df, output_widget=output_widget)

def display_feature_viewer(accession, file_name="protvista_viewer1.html", width="1000", height="600"):
    """
    Display Protein structure, sequence, domain organization and mutation(s) for a given target using ProtVista
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>ProtVista Viewer</title>
        <script src="https://cdn.jsdelivr.net/npm/whatwg-fetch@3.0.0/dist/fetch.umd.min.js"></script>
        <script src="https://d3js.org/d3.v4.min.js"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/litemol@2.4.2/dist/css/LiteMol-plugin.min.css">
        <script src="https://cdn.jsdelivr.net/npm/litemol@2.4.2/dist/js/LiteMol-plugin.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@webcomponents/webcomponentsjs@2.2.10/webcomponents-bundle.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@webcomponents/webcomponentsjs@2.2.10/custom-elements-es5-adapter.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@babel/polyfill@7.4.4/dist/polyfill.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/protvista-uniprot@latest/dist/protvista-uniprot.js"></script>
    </head>
    <body>
        <protvista-uniprot accession="{accession}"></protvista-uniprot>
    </body>
    </html>
    """

    with open(file_name, "w") as file:
        file.write(html_content)

    display(IFrame(src=file_name, width=width, height=height))

def display_target_info(api_response):
    """
    Displays protein information extracted from an API response in a formatted HTML table.
    """
    if not api_response or 'results' not in api_response or not api_response['results']:
        print("Invalid or empty API response.")
        return

    result = api_response['results'][0]
    accession = result.get('primaryAccession', 'N/A')
    protein_name = result.get('proteinDescription', {}).get('recommendedName', {}).get('fullName', {}).get('value', 'N/A')
    gene_name = result.get('genes', [{}])[0].get('geneName', {}).get('value', 'N/A')
    status = result.get('entryType', 'N/A')
    organism = result.get('organism', {}).get('scientificName', 'N/A')
    existence = result.get('proteinExistence', 'N/A')
    annotation_score = result.get('annotationScore', 'N/A')

    html_content = f"""
    <table style='width: 100%; border: 1px solid black;'>
        <tr>
            <th style='border: 1px solid black; text-align: center;'>Field</th>
            <th style='border: 1px solid black; text-align: center;'>Value</th>
        </tr>
        <tr>
            <td style='border: 1px solid black; text-align: center;'>Accession</td>
            <td style='border: 1px solid black; text-align: center;'>{accession}</td>
        </tr>
        <tr>
            <td style='border: 1px solid black; text-align: center;'>Protein</td>
            <td style='border: 1px solid black; text-align: center;'>{protein_name}</td>
        </tr>
        <tr>
            <td style='border: 1px solid black; text-align: center;'>Gene</td>
            <td style='border: 1px solid black; text-align: center;'>{gene_name}</td>
        </tr>
        <tr>
            <td style='border: 1px solid black; text-align: center;'>Status</td>
            <td style='border: 1px solid black; text-align: center;'>{status}</td>
        </tr>
        <tr>
            <td style='border: 1px solid black; text-align: center;'>Organism</td>
            <td style='border: 1px solid black; text-align: center;'>{organism}</td>
        </tr>
        <tr>
            <td style='border: 1px solid black; text-align: center;'>Protein Existence</td>
            <td style='border: 1px solid black; text-align: center;'>{existence}</td>
        </tr>
        <tr>
            <td style='border: 1px solid black; text-align: center;'>Annotation Score</td>
            <td style='border: 1px solid black; text-align: center;'>{annotation_score}</td>
        </tr>
    </table>
    """

    display(HTML(html_content))

def display_organism_taxonomy_details(api_response):
    """
    Displays organism Taxonomy details.
    """
    result = api_response['results'][0]
    organism_info = result['organism']
    taxon_id = organism_info.get('taxonId', 'N/A')
    scientific_name = organism_info.get('scientificName', 'N/A')
    common_name = organism_info.get('commonName', 'N/A')
    lineage = organism_info.get('lineage', [])

    lineage_links = ' > '.join([f"<a href='https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?name={term.replace(' ', '+')}' target='_blank'>{term}</a>" for term in lineage])

    data = [
        ["Taxonomic identifier", f"<a href='https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={taxon_id}' target='_blank'>{taxon_id} NCBI</a>"],
        ["Organism", f"{scientific_name} ({common_name})"],
        ["Taxonomic lineage", lineage_links]
    ]

    df = pd.DataFrame(data, columns=["Field", "Value"])

    display(HTML(df.to_html(escape=False, index=False, classes='table table-striped table-bordered')))

    custom_css = """
    <style>
    .table {
        font-size: 18px;
        text-align: center;
    }
    .table th, .table td {
        text-align: center;
        vertical-align: middle;
    }
    </style>
    """
    display(HTML(custom_css))


def display_topology_table(api_response):
    """
    Display taxonomy from subcellular section in uniprot, with dynamic updates based on dropdown selection.
    """
    data = []
    for feature in api_response[0]['features']:
        if feature['category'] == 'TOPOLOGY':
            type_ = feature['type']
            if type_ == 'TOPO_DOM':
                type_ = 'Topological domain'
            elif type_ == 'TRANSMEM':
                type_ = 'Transmembrane'
            positions = f"{feature['begin']}-{feature['end']}"
            description = feature['description']
            code = feature['evidences'][0]['code']
            accession = api_response[0]['accession']
            description_link = f'<a href="https://www.ebi.ac.uk/QuickGO/term/{code}" target="_blank">{description}</a>'
            blast_link = f'<a href="https://www.uniprot.org/blast?ids={accession}[{feature["begin"]}-{feature["end"]}]" target="_blank">blast</a>'
            data.append([type_, positions, description_link, blast_link])

    df = pd.DataFrame(data, columns=["TYPE", "Positions", "Description", "Blast"])
    output_space = widgets.Output()

    def update_table(change):
        with output_space:
            clear_output(wait=True)
            filter_type = change.new if change else "All"
            if filter_type == "All":
                filtered_df = df
            else:
                filtered_df = df[df["TYPE"] == filter_type]
            display(HTML(filtered_df.to_html(escape=False, index=False, classes='table table-striped table-bordered')))

    dropdown = widgets.Dropdown(
        options=["All", "Topological domain", "Transmembrane"],
        value="All",
        description="TYPE:",
        style={'description_width': 'initial'}
    )
    dropdown.observe(update_table, names='value')

    display(dropdown)
    update_table(None)  
    display(output_space)

    custom_css = """
    <style>
    .table {
        font-size: 18px;
        text-align: center;
    }
    .table th, .table td {
        text-align: center;
        vertical-align: middle;
    }
    </style>
    """
    display(HTML(custom_css))


def process_and_display_knowndrugs(api_response):
    """
    Processes KnownDrugs API response to filter the latest phase entries of drug data and display it.
    """

    target_id = api_response['data']['target']['id']
    known_drugs = api_response['data']['target']['knownDrugs']

    if known_drugs['count'] == 0:
        print(f"No known drugs found for {target_id}")
        return
    
    def phase_to_number(phase):
        mapping = {
            'Phase IV': 4,
            'Phase III': 3,
            'Phase II': 2,
            'Phase I (Early)': 1.1,
            'Phase I': 1,
            'N/A': 0
        }
        return mapping.get(phase, 0)
    
    def status_priority(status):
        priorities = {
            'Completed': 8,
            'Terminated': 7,
            'Suspended':6,
            'Withdrawn': 5,
            'Recruiting': 4,
            'Active, not recruiting': 3,
            'Not yet recruiting': 2,
            'N/A': 1
        }
        return priorities.get(status, -1)

    def get_sponsor_name(url):
        nct_id = url.split('/')[-1] if 'clinicaltrials.gov' in url else None
        if not nct_id:
            return "URL Invalid or Not Applicable"
        
        api_url = f"https://clinicaltrials.gov/api/int/studies/{nct_id}?history=true"
        try:
            response = requests.get(api_url)
            response_data = response.json()
            sponsor_name = response_data['study']['protocolSection']['identificationModule']['organization']['fullName']
            return sponsor_name
        except Exception as e:
            print(f"Failed to fetch sponsor from {api_url}: {str(e)}")
            return "Unknown"

    def get_latest_phase_entries(data):
        temp_entries = {}
        for entry in data:
            key = (entry['drug']['id'], entry['disease']['id'])
            phase_num = phase_to_number(entry['phase'])
            status_pri = status_priority(entry.get('status', 'N/A'))
            entry_value = (phase_num, status_pri, entry)

            if key not in temp_entries:
                temp_entries[key] = [entry_value]
            else:
                temp_entries[key].append(entry_value)
        
        filtered_entries = {}
        for key, values in temp_entries.items():
            max_phase = max([v[0] for v in values])
            max_phase_entries = [v for v in values if v[0] == max_phase]
            highest_priority_entry = max(max_phase_entries, key=lambda x: x[1])
            filtered_entries[key] = highest_priority_entry[2]

        return list(filtered_entries.values())

    data = api_response['data']['target']['knownDrugs']['rows']
    latest_phase_entries = get_latest_phase_entries(data)

    def create_dataframe(entries):
        if not entries:
            return pd.DataFrame()
        dataframe = pd.DataFrame({
            'Drug': [entry['drug']['name'] for entry in entries],
            'Drug Link': [f'<a href="https://platform.opentargets.org/drug/{entry["drug"]["id"]}">{entry["drug"]["name"]}</a>' for entry in entries],
            'Type': [entry['drugType'] for entry in entries],
            'Mechanism of Action': [entry['mechanismOfAction'] for entry in entries],
            'Disease': [entry['disease']['name'] for entry in entries],
            'Disease Link': [f'<a href="https://platform.opentargets.org/disease/{entry["disease"]["id"]}">{entry["disease"]["name"]}</a>' for entry in entries],
            'Phase': [f'Phase {entry["phase"]}' for entry in entries],
            'Status': [entry['status'] or 'N/A' for entry in entries],
            'Source Link': [', '.join([f'<a href="{url["url"]}">{url["name"]}</a>' for url in entry['urls']]) for entry in entries],
            'Sponsor': [get_sponsor_name(', '.join([url['url'] for url in entry['urls']])) if any('clinicaltrials.gov' in url['url'] for url in entry['urls']) else "-NA-" for entry in entries]
        })
        dataframe.index = range(1, len(dataframe) + 1)
        return dataframe

    df = create_dataframe(latest_phase_entries)

    def filtered_table(drug_id, disease_id, sponsor):
        filter_condition = df
        if drug_id != 'All':
            filter_condition = filter_condition[filter_condition['Drug'] == drug_id]
        if disease_id != 'All':
            filter_condition = filter_condition[filter_condition['Disease'] == disease_id]
        if sponsor != 'All':
            filter_condition = filter_condition[filter_condition['Sponsor'] == sponsor]
        display(HTML(filter_condition[['Drug Link', 'Type', 'Mechanism of Action', 'Disease Link', 'Phase', 'Status', 'Source Link', 'Sponsor']].to_html(escape=False)))

    drug_dropdown = widgets.Dropdown(options=['All'] + sorted(df['Drug'].unique()), description='Drug:')
    disease_dropdown = widgets.Dropdown(options=['All'] + sorted(df['Disease'].unique()), description='Disease:')
    sponsor_dropdown = widgets.Dropdown(options=['All'] + sorted(df['Sponsor'].unique()), description='Sponsor:')

    out = widgets.interactive_output(filtered_table, {'drug_id': drug_dropdown, 'disease_id': disease_dropdown, 'sponsor': sponsor_dropdown})

    display(widgets.HBox([drug_dropdown, disease_dropdown, sponsor_dropdown]))
    display(out)


def display_safety_events(api_response):
    safety_liabilities = api_response['data']['target']['safetyLiabilities']
    
    if not safety_liabilities:
        print("No Safety events found for target")
        return pd.DataFrame()
    
    entries = []
    for event in safety_liabilities:
        biosystems = ', '.join([
            f'<a href="https://identifiers.org/{sample["tissueId"].replace("_", ":")}">{sample["tissueLabel"]}</a>'
            for sample in event['biosamples']
        ])
        direction = event['effects'][0]['direction']
        dosing = event['effects'][0]['dosing']
        dosing_effect = f"<b>Direction:</b> {direction}<br><b>Dosing:</b> {dosing}"
        event_hyperlink = f'<a href="https://platform.opentargets.org/disease/{event["eventId"]}" style="font-size: 12px;">{event["event"]}</a>' if event['eventId'] else event['event']
        
        if event['url']:
            source = f'<a href="{event["url"]}" style="font-size: 14px;">{event["datasource"]}</a>'
        elif event['literature']:
            literature_link = f"https://europepmc.org/abstract/med/{event['literature']}"
            source = f'<a href="{literature_link}" style="font-size: 14px;">{event["datasource"]}</a>'
        else:
            source = event['datasource']
        
        entries.append([
            event_hyperlink,
            biosystems,
            dosing_effect,
            'N/A' if not event['studies'] else event['studies'],
            source
        ])
    
    dataframe = pd.DataFrame({
        'Safety event': [entry[0] for entry in entries],
        'Biosystems': [entry[1] for entry in entries],
        'Dosing effect': [entry[2] for entry in entries],
        'Experimental Studies': [entry[3] for entry in entries],
        'Source': [entry[4] for entry in entries]
    })
    
    dataframe.index = range(1, len(dataframe) + 1)
    display(HTML(dataframe.to_html(escape=False, index=False)))