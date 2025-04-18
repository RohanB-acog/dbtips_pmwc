TargetAssociationsQuery = """query TargetAssociationsQuery(
  $id: String!
  $index: Int!
  $size: Int!
  $sortBy: String!
  $enableIndirect: Boolean!
  $datasources: [DatasourceSettingsInput!]
  $rowsFilter: [String!]
  $facetFilters: [String!]
) {
  target(ensemblId: $id) {
    id
    approvedSymbol
    associatedDiseases(
      page: { index: $index, size: $size }
      orderByScore: $sortBy
      enableIndirect: $enableIndirect
      datasources: $datasources
      Bs: $rowsFilter
      facetFilters: $facetFilters
    ) {
      count
      rows {
        disease {
          id
          name
        }
        score
        datasourceScores {
          componentId: id
          score
        }
      }
    }
  }
}

"""

DiseaseAssociationsQuery = """query DiseaseAssociationsQuery(
  $id: String!
  $index: Int!
  $size: Int!
  $filter: String
  $sortBy: String!
  $enableIndirect: Boolean!
  $datasources: [DatasourceSettingsInput!]
  $rowsFilter: [String!]
) {
  disease(efoId: $id) {
    id
    name
    associatedTargets(
      page: { index: $index, size: $size }
      orderByScore: $sortBy
      BFilter: $filter
      enableIndirect: $enableIndirect
      datasources: $datasources
      Bs: $rowsFilter
    ) {
      count
      rows {
        target {
          id
          approvedSymbol
          approvedName
          prioritisation {
            items {
              key
              value
            }
          }
        }
        score
        datasourceScores {
          componentId: id
          score
        }
      }
    }
  }
}"""

DiseaseDescendantsQuery = """query DiseaseDescendantsQuery(
  $id: String!
) {
  disease(efoId: $id) {
    id
    name
    descendants
  }
}"""

DiseaseSynonymsQuery = """query DiseaseSynonymsQuery(
  $id:String!
) {
  disease(efoId: $id) {
    synonyms{
      relation
      terms
    }
    children{
      synonyms{
        relation
        terms
      }
    }
  }
}"""

GenePageL2GPipelineQuery = """query GenePageL2GPipelineQuery($geneId: String!) {
  geneInfo(geneId: $geneId) {
    id
    symbol
    chromosome
    start
    end
    bioType
    __typename
  }
  studiesAndLeadVariantsForGeneByL2G(geneId: $geneId) {
    pval
    yProbaModel
    study {
      studyId
      traitReported
      traitEfos
      pubAuthor
      pubDate
      pmid
      nInitial
      nReplication
      hasSumstats
      nCases
      __typename
    }
    variant {
      rsId
      id
      __typename
    }
    odds {
      oddsCI
      oddsCILower
      oddsCIUpper
      __typename
    }
    beta {
      betaCI
      betaCILower
      betaCIUpper
      direction
      __typename
    }
    __typename
  }
}"""

GeneOntologyQuery = """query GeneOntology($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    geneOntology {
      term {
        id
        name
      }
      aspect
      evidence
      geneProduct
      source
    }
  }
}
"""

TargetDescriptionQuery = """query GetTargetDescription($id: String!) {
  target(ensemblId: $id) {
    id
    synonyms {
      label
      source
    }
    functionDescriptions
  }
}
"""

MousePhenotypesQuery = """query MousePhenotypes($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    mousePhenotypes {
      targetInModel
      targetInModelMgiId
      modelPhenotypeId
      modelPhenotypeLabel
      modelPhenotypeClasses {
        id
        label
      }
      biologicalModels {
        id
        allelicComposition
        geneticBackground
        literature
      }
    }
  }
}
"""

TargetabilityQuery = """query TargetabilityQuery(
  $id: String!
  $index: Int!
  $size: Int!
  $filter: String
  $sortBy: String!
  
  $enableIndirect: Boolean!
  $rowsFilter: [String!]
) {
  disease(efoId: $id) {
    id
    name
    associatedTargets(
      page: { index: $index, size: $size }
      orderByScore: $sortBy
      BFilter: $filter
      
      enableIndirect: $enableIndirect
      Bs: $rowsFilter
    ) {
      count
      rows {
        target {
          id
          approvedSymbol
          approvedName
          prioritisation {
            items {
              key
              value
            }
          }
        }
        score
      }
    }
  }
}
"""

TractabilityQuery = """query TractabilityQuery($id: String!) {
  target(ensemblId: $id) {
    id
    tractability {
      value
      modality
      label
    }
  }
}
"""

CompGenomicsQuery = """query CompGenomicsQuery($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    homologues {
      speciesId
      speciesName
      homologyType
      isHighConfidence
      targetGeneId
      targetGeneSymbol
      queryPercentageIdentity
      targetPercentageIdentity
    }
  }
}
"""

DifferentialRNAQuery = """query DifferentialRNAQuery($id: String!) {
  target(ensemblId: $id) {
    id
    expressions {
      tissue{
        anatomicalSystems
        id
        label
        organs
      }
      rna {
        level
        unit
        value
        zscore
      }
      protein {
        level
        reliability
      }
    }
  }
}
"""

GetTargetUniProt = """query GetTargetUniProt($id: String!) {
  target(ensemblId: $id) {
    id
    proteinIds {
      id
      source
    }
  }
}
"""

KnownDrugsQuery = """query KnownDrugsQuery(
  $id: String!
  $cursor: String
  $freeTextQuery: String
  $size: Int = 5000
) {
  target(ensemblId: $id) {
    id
    knownDrugs(cursor: $cursor, freeTextQuery: $freeTextQuery, size: $size) {
      count
      cursor
      rows {
        phase
        status
        urls {
          name
          url
        }
        disease {
          id
          name
        }
        drug {
          id
          name
          isApproved
          approvedIndications
          hasBeenWithdrawn
          mechanismsOfAction {
            rows {
              actionType
              targets {
                id
              }
            }
          }
        }
        drugType
        mechanismOfAction
      }
    }
  }
}
"""

SafetyQuery = """query Safety($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    safetyLiabilities {
      event
      eventId
      biosamples {
        cellFormat
        cellLabel
        tissueLabel
        tissueId
      }
      effects {
        dosing
        direction
      }
      studies {
        name
        type
        description
      }
      datasource
      literature
      url
    }
  }
}
"""

PublicationQuery = """
query PublicationQuery(
  $ensemblIds: [String!]!
  $efoId: String!
  $size: Int!
  $cursor: String
) {
  disease(efoId: $efoId) {
    id
    europePmc: evidences(
      ensemblIds: $ensemblIds
      enableIndirect: true
      size: $size
      datasourceIds: ["europepmc"]
      cursor: $cursor
    ) {
      count
      cursor
      rows {
        disease {
          name
          id
        }
        target {
          approvedSymbol
          id
        }
        literature
      }
    }
  }
}
"""

DiseaseKnownDrugs = """query DiseaseKnownDrugsQuery(
  $efoId: String!
  $cursor: String
  $freeTextQuery: String
  $size: Int = 5000
) {
  disease(efoId: $efoId) {
    id
    knownDrugs(cursor: $cursor, freeTextQuery: $freeTextQuery, size: $size) {
      count
      cursor
      rows {
        phase
        status
        urls {
          name
          url
        }
        disease {
          id
          name
        }
        drug {
          id
          name
          isApproved
          approvedIndications
          hasBeenWithdrawn
          mechanismsOfAction {
            rows {
              actionType
              targets {
                id
              }
            }
          }
        }
        urls {
          url
          name
        }
        drugType
        mechanismOfAction
        target {
          id
          approvedName
          approvedSymbol
        }
      }
    }
  }
}
"""

TargetExpressionQuery: str = """
query targetAnnotation($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    expressions {
      tissue {
        id
        label
        anatomicalSystems
        organs
      }
      rna {
        zscore
        unit
        value
        level
      }
      protein {
        reliability
        level
        cellType {
          reliability
          name
          level
        }
      }
    }
  }
}
"""

DiseaseAssociatedTargetQuery = """
query DiseaseAssociationsQuery(
    $id: String!,
    $index: Int!,
    $size: Int!,
    $sortBy: String!,
    $enableIndirect: Boolean!,
    $datasources: [DatasourceSettingsInput!],
    $rowsFilter: [String!],
    $facetFilters: [String!]
) {
    disease(efoId: $id) {
        associatedTargets(
          page: { index: $index, size: $size }
          orderByScore: $sortBy
          enableIndirect: $enableIndirect
          datasources: $datasources
          Bs: $rowsFilter
          facetFilters: $facetFilters
        ) {
            rows {
                target {
                    id
                }
            }
        }
    }
}
"""
GeneEssentialityMapTargetQuery = """
query Depmap($ensemblId: String!) {
              target(ensemblId: $ensemblId) {
                depMapEssentiality {
                  tissueName
                  screens {
                    depmapId
                    cellLineName
                    diseaseFromSource
                    geneEffect
                    expression
                  }
                }
              }
            }
"""