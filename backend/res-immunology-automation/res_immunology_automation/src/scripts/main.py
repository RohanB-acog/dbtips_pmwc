import ipywidgets as widgets
from ipywidgets import interact, VBox, Dropdown, Output
from IPython.display import display, clear_output, HTML, IFrame, Markdown
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.colors import Normalize
from matplotlib.cm import viridis
import requests
import seaborn as sns
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from target_analyzer import TargetAnalyzer
from helper import *
import warnings
warnings.filterwarnings('ignore')

class TargetDiseaseAnalyzerApp:
    def __init__(self):
        self.output = Output()
        self.target_input = widgets.Text(description='Target Gene:')
        self.analyze_button = widgets.Button(description='Analyze Target')
        self.analyze_button.on_click(self.perform_analysis)
        self.main_container = widgets.VBox([self.target_input, self.analyze_button, self.output])
        display(self.main_container)

    def perform_analysis(self, _):
        with self.output:
            clear_output(wait=True)
            target = self.target_input.value.strip()
            if not target:
                display(Markdown('Please enter a target gene name.'))
                return
            analyzer = TargetAnalyzer(target)
            self.display_all_information(analyzer)

    def display_all_information(self, analyzer):
        display(Markdown('### Target Introduction'))
        display(Markdown('##### '))
        api_response = analyzer.get_target_introduction()
        display_target_info(api_response)
        display(Markdown('### Target Description'))
        display(Markdown('##### '))
        description_response = analyzer.get_target_description()
        display_target_information(description_response)


        display(Markdown('### Taxonomy'))
        display(Markdown('##### '))
        display_organism_taxonomy_details(api_response)

        display(Markdown('### Disease Association'))
        display(Markdown('##### '))
        setup_disease_selection_interface(analyzer.target)

        display(Markdown('### Targetability'))
        display(Markdown('##### '))
        targetability_response = analyzer.get_targetablitiy()
        parse_and_plot_targetability(targetability_response,self.target_input.value)

        display(Markdown('### Tractability'))
        display(Markdown('##### '))
        tractability_response = analyzer.get_tractability()
        plot_tractability(tractability_response)

        display(Markdown('### Target Ontology'))
        display(Markdown('##### '))
        ontology_response = analyzer.get_target_ontology()
        ontology_df = parse_gene_ontology(ontology_response)
        display(HTML(ontology_df.to_html(escape=False)))

        display_go_ribbon(analyzer.hgnc_id)

        display(Markdown('### Mouse Phenotypes'))
        display(Markdown('##### '))
        mouse_phenotypes_response = analyzer.get_mouse_phenotypes()
        parse_mouse_phenotypes(mouse_phenotypes_response)

        display(Markdown('### Paralogs'))
        display(Markdown('##### '))
        comparative_genomics_response = analyzer.get_paralogs()
        display_paralogs(comparative_genomics_response)

        display(Markdown('### Differential RNA/Protein Expressions'))
        display(Markdown('##### '))
        expression_response = analyzer.get_differential_rna_and_protein_expression()
        df = prepare_data(expression_response['data']['target']['expressions'])
        setup_interactive_plot(df)

        display(Markdown('### Protein Structure and Organization'))
        display(Markdown('##### '))
        display_feature_viewer(analyzer.uniprot_id)

        display(Markdown('### Subcellular Section'))
        display(Markdown('##### '))
        topology_features_response = analyzer.get_target_topology_features()
        display_topology_table(topology_features_response)
        
        display(Markdown('### Known Drugs'))
        display(Markdown('##### '))
        knowndrugs_response = analyzer.get_known_drugs()
        process_and_display_knowndrugs(knowndrugs_response)
        
        display(Markdown('### Safety Events'))
        display(Markdown('##### '))
        safety_response = analyzer.get_safety()
        display_safety_events(safety_response)