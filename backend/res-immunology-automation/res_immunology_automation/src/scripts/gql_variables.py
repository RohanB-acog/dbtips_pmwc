DiseaseAssociationQueryVariables = """{
  "id": "{efo_id}",
  "index": 0,
  "size": 500,
  "filter": "",
  "sortBy": "{sort_by}",
  "enableIndirect": false,
  "datasources": [
    {
      "id": "ot_genetics_portal",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "gene_burden",FGF
      "weight": 1,
      "propagate": true
    },
    {
      "id": "eva",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "genomics_england",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "gene2phenotype",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "uniprot_literature",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "uniprot_variants",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "orphanet",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "clingen",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "cancer_gene_census",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "intogen",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "eva_somatic",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "cancer_biomarkers",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "chembl",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "crispr_screen",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "crispr",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "slapenrich",
      "weight": 0.5,
      "propagate": true
    },
    {
      "id": "progeny",
      "weight": 0.5,
      "propagate": true
    },
    {
      "id": "reactome",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "sysbio",
      "weight": 0.5,
      "propagate": true
    },
    {
      "id": "europepmc",
      "weight": 0.2,
      "propagate": true
    },
    {
      "id": "expression_atlas",
      "weight": 0.2,
      "propagate": true
    },
    {
      "id": "impc",
      "weight": 0.2,
      "propagate": true
    },
    {
      "id": "ot_crispr_validation",
      "weight": 0.5,
      "propagate": true
    },
    {
      "id": "ot_crispr",
      "weight": 0.5,
      "propagate": true
    },
    {
      "id": "encore",
      "weight": 0.5,
      "propagate": true
    }
  ],
  "entity": "target"
}"""

TargetAssociationQueryVariables = """{
  "id": "{ensembl_id}",
  "index": 0,
  "size": 1000,
  "filter": "",
  "sortBy": "{sort_by}",
  "enableIndirect": false,
  "datasources": [
    {
      "id": "ot_genetics_portal",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "gene_burden",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "eva",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "genomics_england",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "gene2phenotype",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "uniprot_literature",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "uniprot_variants",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "orphanet",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "clingen",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "cancer_gene_census",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "intogen",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "eva_somatic",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "cancer_biomarkers",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "chembl",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "crispr_screen",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "crispr",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "slapenrich",
      "weight": 0.5,
      "propagate": true
    },
    {
      "id": "progeny",
      "weight": 0.5,
      "propagate": true
    },
    {
      "id": "reactome",
      "weight": 1,
      "propagate": true
    },
    {
      "id": "sysbio",
      "weight": 0.5,
      "propagate": true
    },
    {
      "id": "europepmc",
      "weight": 0.2,
      "propagate": true
    },
    {
      "id": "expression_atlas",
      "weight": 0.2,
      "propagate": true
    },
    {
      "id": "impc",
      "weight": 0.2,
      "propagate": true
    },
    {
      "id": "ot_crispr_validation",
      "weight": 0.5,
      "propagate": true
    },
    {
      "id": "ot_crispr",
      "weight": 0.5,
      "propagate": true
    },
    {
      "id": "encore",
      "weight": 0.5,
      "propagate": true
    }
  ],
  "entity": "target"
}
"""

GeneOntologyVariables = """{
  "ensemblId": "{ensembl_id}"
}
"""

TargetabilityVariables = """{
  "id": "{efo_id}",
  "index": 0,
  "size": 3300,
  "filter": "{target}",
  "sortBy": "score",
  "enableIndirect": true
}
"""

PublicationVariables = """{
  "ensemblId": "{ensembl_id}",
  "efoId": "{efo_id}",
  "size": 50
}
"""

DiseaseAnnotationQueryVariables = """
query diseaseAnnotation($efoIds: [String!]!) {
    diseases(efoIds: $efoIds) {
        id
        name
        description 
        synonyms {
            relation
            terms
        }
    }
}
"""

SearchQuery = """
query searchWithPagination($queryString: String!, $entityNames: [String!]!, $page: Pagination!) {
  search(queryString: $queryString, entityNames: $entityNames, page: $page) {
    hits {
      id
      name
      entity
      description
    }
  }
}
"""

DiseaseAssociationTargetVariables="""{
  "id": "{efo_id}",
  "index": 0,
  "size": 5000,
  "sortBy": "{sort_by}",
  "enableIndirect": true,
  "datasources": [
    {
      "id": "ot_genetics_portal",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "gene_burden",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "eva",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "genomics_england",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "gene2phenotype",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "uniprot_literature",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "uniprot_variants",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "orphanet",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "clingen",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "cancer_gene_census",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "intogen",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "eva_somatic",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "cancer_biomarkers",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "chembl",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "crispr_screen",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "crispr",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "slapenrich",
      "weight": 0.5,
      "propagate": true,
      "required": false
    },
    {
      "id": "progeny",
      "weight": 0.5,
      "propagate": true,
      "required": false
    },
    {
      "id": "reactome",
      "weight": 1,
      "propagate": true,
      "required": false
    },
    {
      "id": "sysbio",
      "weight": 0.5,
      "propagate": true,
      "required": false
    },
    {
      "id": "europepmc",
      "weight": 0.2,
      "propagate": true,
      "required": false
    },
    {
      "id": "expression_atlas",
      "weight": 0.2,
      "propagate": true,
      "required": false
    },
    {
      "id": "impc",
      "weight": 0.2,
      "propagate": true,
      "required": false
    },
    {
      "id": "ot_crispr_validation",
      "weight": 0.5,
      "propagate": true,
      "required": false
    },
    {
      "id": "ot_crispr",
      "weight": 0.5,
      "propagate": true,
      "required": false
    },
    {
      "id": "encore",
      "weight": 0.5,
      "propagate": true,
      "required": false
    }
  ],
  "entity": "disease"
}
"""
GeneEssentialityMapTargetVariable= """ {
  "ensemblId": "{ensembl_id}"  
}
"""