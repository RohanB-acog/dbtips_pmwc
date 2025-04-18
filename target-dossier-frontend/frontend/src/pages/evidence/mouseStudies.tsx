import { Empty, Select } from "antd";
import parse from "html-react-parser";

import { fetchData } from "../../utils/fetchData";
import { useQuery } from "react-query";
import ExportButton from "../../components/testExportButton";
import { useState } from "react";
import Table from "../../components/testTable";
const { Option } = Select;
// const CustomHeader = (props) => {
// 	return (
// 		<>
// 		 <span>{props.displayName}</span>
// 		<Dropdown
// 			dropdownRender={() => (
// 				<div className=' bg-white p-[30px] max-w-[640px] border shadow rounded-md'>
// 					<div className='mt-2'>
// 						<h1 className=' text-lg font-semibold'>
// 							1. Tnfrsf4<sup>tm1nik</sup>
// 						</h1>

// 						<p>
// 							<b>Mutation Name:</b>
// 							tumor necrosis factor receptor superfamily, member 4; targeted
// 							mutation 1, Nigel Killeen
// 						</p>
// 						<p>
// 							<b>Mutation Type:</b>
// 							Insertion, Intragenic deletion
// 						</p>

// 						<p>
// 							<b>Method:</b> A neomycin cassette was used to replace four
// 							exons, which code for the first 143 amino acids of the
// 							protein. Activated T cells from homozygous mutant animals
// 							lacked expression of Tnfrsf4 as detected by flow cytometry
// 							with the OX86 mAb as well as a soluable ligand fusion protein.
// 						</p>
// 					</div>
// 					<div className='mt-2'>
// 						<h1 className=' text-lg font-semibold'>
// 							2. Tnfrsf4<sup>tm1Mfb</sup>
// 						</h1>

// 						<p>
// 							<b>Mutation Name:</b>
// 							tumor necrosis factor receptor superfamily, member 4; targeted
// 							mutation 1, Martin F Bachmann
// 						</p>
// 						<p>
// 							<b>Mutation Type:</b>Insertion
// 						</p>
// 						<p>
// 							<b> Method:</b> A vector targeting Tnfrsf4 was created to
// 							introduce a stop codon at amino acid 150. A neomycin
// 							resistance cassette was also included in the vector for
// 							selection purposes.
// 						</p>
// 					</div>
// 				</div>
// 			)}
// 		>
// 			<span className='material-symbols-outlined ml-1 text-lg cursor-pointer align-middle'>info</span>
// 		</Dropdown>
// 		</>
// 	);
// };
const ModelStudies = ({ target }) => {
  const [selectedCategory, setSelectedCategory] = useState("All");
  const payload = {
    target: target,
  };

  const {
    data: mouseStudiesData,
    error: mouseStudiesError,
    isLoading,
  } = useQuery(
    ["mouseStudies", payload],
    () => fetchData(payload, "/evidence/target-mouse-studies/"),
    {
      enabled: !!target,
    }
  );

  const rowData: MousePhenotypeEntry[] = mouseStudiesData
    ? Object.values(mouseStudiesData?.mouse_studies)
    : [];
  console.log("rowData mouse studies", rowData);
  const filteredData = rowData.filter((item) => {
    if (selectedCategory === "All") {
      return true;
    }
    return item.Categories.some((el) => el.Label.includes(selectedCategory));
  });
  return (
    <section id="model-studies" className="mt-12  bg-gray-50 px-[5vw] py-10">
      <div className="flex items-center gap-x-2">
        <h1 className="text-3xl font-semibold">
          Target perturbation phenotypes
        </h1>
      </div>

      <p className="mt-2  font-medium">
        Target perturbation phenotypes in mouse models help biopharma scientists
        understand a target’s role in disease, validate its therapeutic
        potential, and assess safety and efficacy in vivo.
      </p>

      {mouseStudiesError ? (
        <div className="mt-4  max-h-[280px] flex items-center justify-center">
          <Empty description={String(mouseStudiesError)} />
        </div>
      ) : (
        <div>{ filteredData.length>0 &&
          <div className="flex justify-between my-2">
            <div>
              <span className="mt-10 mr-1">Filter by phenotypes: </span>
              <Select
                defaultValue="All"
                style={{ width: 300 }}
                onChange={(value) => setSelectedCategory(value)}
              >
                <Option value="All">All</Option>
                <Option value="immune system phenotype">
                  Immune system phenotype
                </Option>
              </Select>
            </div>
            <ExportButton
              target={target}
              endpoint={"/evidence/target-mouse-studies/"}
              fileName="Target-perturbation-phenotypes"
              disabled={rowData.length == 0 || isLoading}
            />
          </div>}
          <div className="mt-4">
            <Table
              columnDefs={[
                // {
                // 	field: 'Gene',
                // 	valueGetter: (params) => {
                // 		return params.data?.Gene?.Name;
                // 	},
                // 	cellRenderer: (params) => {
                // 		if (params.data?.Gene?.Link) {
                // 			return <a href={params.data.Gene.Link}>{params.value}</a>;
                // 		}
                // 		return params.value;
                // 	},
                // },
                {
                  field: "Phenotype",
                  flex: 2.3,
                  valueGetter: (params) => {
                    return params.data?.Phenotype?.Label;
                  },
                  // cellRenderer: (params) => {
                  // 	if (params.data?.Phenotype?.Link) {
                  // 		return (
                  // 			<a target='_blank' href={params.data.Phenotype.Link}>
                  // 				{params.value}
                  // 			</a>
                  // 		);
                  // 	}
                  // 	return params.value;
                  // },
                },
                {
                  field: "Categories",
                  valueGetter: (params) => {
                    return params.data?.Categories?.map((el) => el.Label);
                  },

                  // cellRenderer: (params) => {
                  // 	return params.data?.Categories?.map((value, index) => {
                  // 		return (
                  // 			<a
                  // 				key={index}
                  // 				className='mr-2'
                  // 				href={value.Link}
                  // 				target='_blank'
                  // 			>
                  // 				{value.Label}
                  // 				{params.value.length - 1 !== index ? ',' : ''}
                  // 			</a>
                  // 		);
                  // 	});
                  // },
                  flex: 3,
                },

                {
                  field: "Allelic Compositions",
                  flex: 3,
                  headerName: "Allelic compositions",
                  // headerComponentParams: {
                  // 	displayName: 'Allelic Compositions',
                  // },
                  // headerComponent: CustomHeader,
                  valueGetter: (params) => {
                    return (
                      params.data &&
                      params.data["Allelic Compositions"]?.map(
                        (el) => el.Composition
                      )
                    );
                  },
                  cellRenderer: (params) => {
                    return (
                      params.data &&
                      params.data["Allelic Compositions"]?.map(
                        (value, index) => {
                          // Replace terms enclosed in < > with their superscript equivalent
                          const str = value.Composition.replace(
                            /<([^>]+)>/g,
                            (_, match) => `<sup>${match}</sup>`
                          );
                          return (
                            <a
                              key={index}
                              className="mr-2"
                              href={value.Link}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {parse(str)}
                              {params.value.length - 1 !== index ? "," : ""}
                            </a>
                          );
                        }
                      )
                    );
                  },
                },
              ]}
              rowData={filteredData}
            />
          </div>
        </div>
      )}
    </section>
  );
};

export default ModelStudies;

interface MousePhenotypeEntry {
  Gene: {
    Name: string;
    Link: string;
  };
  Phenotype: {
    Label: string;
    Link: string;
  };
  Categories: {
    Label: string;
    Link: string;
  }[];
  "Allelic Compositions": {
    Composition: string;
    Link: string;
  }[];
}
