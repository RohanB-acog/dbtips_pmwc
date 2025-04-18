rnaseq_all_indications_summary_prompt ="""
Please analyze the rnaseq data on multiple diseases {rnaseq_disease} provided and summarize it by 
`Understanding the Data`
- Use your knowledge of multiple diseases to assess the relevance of the datasets.
- Identify which datasets (eg: scRNA, bulk RNA, microarray) are most useful for finding therapeutic targets across diseases.
`Analyzing Patterns in Samples`
- Examine sample types (tissue or cell types) and sequencing methods to:
i) Identify potential therapeutic targets, or
ii) Understand disease mechanisms.
- Highlight tissue types common to multiple diseases across the datasets.
`Generating Actionable Insights`
- Summarize the most relevant datasets and tissue types for studying one or multiple diseases, focusing on target identification and indication expansion.
- Highlight key insights from datasets that are applicable across diseases.
- Use prior knowledge to offer insights that speed up target identification for drug discovery and development.
- Ensure the summary is based on a thorough analysis of the `ENTIRE DATASET`, without limiting the focus to a subset such as the top rows, to provide comprehensive and accurate conclusions.
"""

rnaseq_data_summary_prompt = """
Please analyze the rnaseq data provided and summarize it by:

- Integrating key insights from datasets  most relevant to target identification in {rnaseq_disease} for a biopharma scientist
- Analyzing the pattern of samples and sequencing methods and the inferences gained in context of either potential therapeutic targets or understanding disease mechanism
- Integrate prior knowledge about {rnaseq_disease} to understand the relevance of the datasets provided.

Integrating these with key insights that assist the scientist in target identification for a disease or multiple disease using common pathways, please generate a summary that includes
- Most relevant datasets for analysis from a biopharma target identification and indication expansion perspective.
- Prior knowledge driven insights that accelerate the scientists work in target identification from a drug discovery and development for one or multiple disease standpoint.
- Ensure the summary is based on a thorough analysis of the ENTIRE DATASET, without limiting the focus to a subset such as the top rows, to provide comprehensive and accurate conclusions.
"""

pipeline_target_summary_prompt="""
Please analyze pipeline by target data and summarize it to deliver a comprehensive overview of the {pipeline_target_target}'s landscape:
- From the dataset, focus on describing the biological role of {pipeline_target_target} and its association with {pipeline_target_diseases}, including its mechanism of action and the therapeutic modalities being investigated, such as small molecules, biologics, or gene therapies
"""

literature_summary_prompt="""
Can you provide mechanistic insights into the role of {literature_target} in the pathogenesis of {literature_diseases}? Specifically, what pathways, biological processes, and cell types are implicated? Are there shared mechanisms across these diseases, and where do they converge or diverge in terms of immune response, tissue remodeling, or disease progression?

Please refer to the following sources for information:
{literature_urls}

**Important Instructions**:
- You must use the data from these references to provide a detailed response.
"""

PROMPT_TEMPLATES = {
    "literature": literature_summary_prompt.strip(),
    "pipeline_target": pipeline_target_summary_prompt.strip()
}

# Common format instructions
FORMAT_INSTRUCTIONS = """
In addition, identify key topics from the data and prior knowledge, and suggest a list of questions for further exploration. This should not be part of above summary. 

You must use the following format for your response only for this question and should not be used for follow up questions:
{format_instructions}
"""

def get_prompt_for_datasets(selected_datasets,context_variables):
    # Handle single widget case
    if len(selected_datasets) == 1:
        dataset = selected_datasets[0]
        if dataset in PROMPT_TEMPLATES:
            if 'disease' in context_variables[dataset]:
                # Perform the length check if 'disease' exists
                prompt = PROMPT_TEMPLATES[f"{dataset}_all"] if len(context_variables[dataset]['disease']) > 1 else PROMPT_TEMPLATES[dataset]
            else:
                # If 'disease' does not exist, use the dataset prompt directly
                prompt = PROMPT_TEMPLATES[dataset]
            return f"{prompt}\n"
        else:
            raise ValueError(f"Unknown dataset: {dataset}")

    # Handle multiple widgets
    combined_prompt = """
Please analyze and summarize the provided datasets by integrating key insights from each dataset, highlighting synergies, differences, and their combined implications. The analysis aims to assist a biopharma scientist in therapeutic target identification, disease understanding, and drug discovery.
"""

    # Add prompts for each selected widget
    for dataset in selected_datasets:
        if dataset in PROMPT_TEMPLATES:
            if 'disease' in context_variables[dataset]:
                prompt = PROMPT_TEMPLATES[f"{dataset}_all"] if len(context_variables[dataset]['disease']) > 1 else PROMPT_TEMPLATES[dataset]
            else:
                prompt = PROMPT_TEMPLATES[dataset]
            combined_prompt += f"\n{prompt}\n"
        else:
            raise ValueError(f"Unknown dataset: {dataset}")

    # Add cross-dataset integration
    combined_prompt += """
**Cross-Dataset Integration:**
- Identify synergies or conflicts between the selected datasets:
  - How do the insights from different datasets complement or contrast with each other?
  - Are there shared pathways or targets that stand out across all datasets?
  - How does integrating these datasets advance understanding of therapeutic target identification and drug discovery?

**Unified Summary:**
- Provide a cohesive summary of the combined datasets, focusing on:
  - Key insights relevant to therapeutic target identification.
  - Disease mechanism understanding and potential indication expansion.
  - Prior knowledge-driven insights that accelerate drug discovery.
"""

    # Append format instructions
    # combined_prompt += f"\n{FORMAT_INSTRUCTIONS}"
    return combined_prompt


# selected_datasets = ["animal_models", "pipeline_indications"]
# selected_datasets = ["animal_models"]

# prompt = get_prompt_for_datasets(selected_datasets)
# print(prompt)