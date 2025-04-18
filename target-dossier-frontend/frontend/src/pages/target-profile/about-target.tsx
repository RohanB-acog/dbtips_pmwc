import { AgGridReact } from "ag-grid-react";
import { Tooltip } from "antd";
// import { InfoCircleOutlined } from "@ant-design/icons";

// import json from '../assets/ADORA3.json';
import { convertObjectToArray } from "../../utils/helper";
import { Empty } from "antd";
import ProteinImage from "./proteinImage";
import LoadingButton from "../../components/loading";

// const InfoWithTooltip = () => (
//   <Tooltip
//     overlayClassName="custom-tooltip"
//     color="#fff"
//     title={`The annotation score provides a heuristic measure of the annotation content of a UniProtKB entry or proteome. This score cannot be used as a measure of the accuracy of the annotation as we cannot define the correct annotation for any given protein.
//     The open-ended interval obtained for these absolute numbers is translated into a 5-point-system by splitting it into 5 sub-intervals. Scores in the first interval are represented by "1 point out of 5", those in the second by "2 points out of 5", etc. An annotation score of 5 points is therefore associated with the best-annotated entries, and a 1-point-score denotes an entry with rather basic annotation`}
//     overlayStyle={{ maxWidth: "350px" }}
//   >
//     <InfoCircleOutlined className=" text-base cursor-pointer ml-1 align-middle" />
//   </Tooltip>
// );
const AboutTarget = ({
  data,
  targetDetailsError,
  targetDetailsLoading,
  description,
}) => {
  // const data = json.about_target;

  const taxonomy = convertObjectToArray(data?.taxonomy) || [];

  return (
    <section id="introduction">
      {/*  Target Introduction */}
      {/* <article id="target-introduction" className="mt-8 px-[5vw]">
        <h1 className="text-3xl font-semibold">Introduction</h1>

        {targetDetailsError ? (
          <div className="ag-theme-quartz mt-4 h-[80vh] max-h-[280px] flex items-center justify-center">
            <Empty />
          </div>
        ) : (
          <div className="mt-4 ag-theme-quartz h-[80vh] max-h-[280px]">
            <AgGridReact
              defaultColDef={{ flex: 1, headerClass: "font-semibold" }}
              columnDefs={[
                {
                  field: "field",
                  cellRenderer: (params) => {
                    if (params.data.field === "Annotation Score") {
                      return (
                        <>
                          {params.value}
                          <InfoWithTooltip />
                        </>
                      );
                    }
                    return params.value;
                  },
                },
                { field: "value" },
              ]}
              rowData={data ? convertObjectToArray(data?.introduction) : null}
            />
          </div>
        )}
      </article> */}

      {/* Target Description */}
      <article id="target-description" className="mt-8 px-[5vw] min-h-[80vh] ">
        <h1 className="text-3xl mb-2 font-semibold ">Description</h1>
        <p className="font-medium">
          This section provides a description of the biological function of the
          target.
        </p>
        {targetDetailsLoading && <LoadingButton />}
        {targetDetailsError && (
          <div className="ag-theme-quartz mt-4 h-[80vh] max-h-[280px] flex items-center justify-center">
            <Empty />
          </div>
        )}
        {/* {
               !targetDetailsError && !targetDetailsLoading && !data && (
                <div>
                <Empty description="No data available" className="flex justify-center items-center flex-col h-[50vh]" />
                </div>       
                )
         } */}
        {data && (
          <>
            {data && (
              <div>
                <span>
                  Uniprot ID:{" "}
                  <span className="text-sky-800">
                    {data.target_details.uniprot_id}
                  </span>{" "}
                  |{" "}
                </span>
                <span>
                  ENSGID:{" "}
                  <span className="text-sky-800">
                    {" "}
                    {data.target_details.ensembl_id}{" "}
                  </span>
                </span>{" "}
              </div>
            )}
            <div className="flex gap-32 mt-3">
              {/* Function Descriptions Section */}
              <div className="flex-1 ">
                <h2 className="text-lg font-medium subHeading">
                  Function descriptions
                </h2>
                <p className="text-justify">{description}</p>
                <h2 className="text-lg font-medium mb-2 mt-10 subHeading">
                  Synonyms (from UniProt)
                </h2>
                <div className="flex flex-wrap gap-2">
                  {data?.summary_and_characteristics?.Synonyms?.[
                    "UniProt Synonyms"
                  ]?.map((synonym, synIndex) => (
                    <Tooltip
                      title="Synonym"
                      key={synIndex}
                      overlayClassName="custom-tooltip"
                      color="#fff"
                    >
                      <div className="px-3 py-1 bg-blue-200 rounded-full text-sm text-gray-700 cursor-pointer">
                        {synonym}
                      </div>
                    </Tooltip>
                  ))}
                </div>
              </div>

              {/* Synonyms Section */}
              <div className="flex-1 mt-[-32px]">
                {data && (
                  <ProteinImage uniprot={data.target_details.uniprot_id} />
                )}
              </div>
            </div>
          </>
        )}
      </article>

      {/* Taxonomy */}
      <article id="taxonomy" className="mt-12 px-[5vw] bg-gray-50 py-20">
        <h1 className="text-3xl font-semibold">Taxonomy</h1>
        <p className=" font-medium mt-2">
          This section provides an identifier for the target unique to an
          organism alongside its taxonomy.
        </p>

        {targetDetailsError ? (
          <div className="ag-theme-quartz mt-4 h-[80vh] max-h-[180px] flex items-center justify-center">
            <Empty />
          </div>
        ) : !targetDetailsError && !targetDetailsLoading && !data ? (
          <div className="h-[40vh] flex items-center justify-center">
            <Empty description="No data available" />
          </div>
        ) : (
          <div className="ag-theme-quartz mt-4 h-[80vh] max-h-[180px]">
            <AgGridReact
              defaultColDef={{
                flex: 1,
                headerClass: "font-semibold",
                autoHeight: true,
                wrapText: true,
                cellStyle: { whiteSpace: "normal", lineHeight: "20px" },
              }}
              columnDefs={[
                { field: "field" },
                {
                  field: "value",
                  cellRenderer: (params) => {
                    if (params.data.field === "Taxonomic Lineage") {
                      const arr = params?.value;
                      return arr.map((link, index) => (
                        <span key={index}>
                          <a
                            target="_blank"
                            href={`https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?name=${link}`}
                          >
                            {link}{" "}
                          </a>{" "}
                          {index < arr.length - 1 && " > "}
                        </span>
                      ));
                    } else if (params.data.field === "Taxonomic Identifier") {
                      return (
                        <a
                          target="_blank"
                          href={`https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=${params.value}`}
                        >
                          {params.value}
                        </a>
                      );
                    }
                    return params.value;
                  },
                },
              ]}
              rowData={data ? taxonomy : null}
              enableRangeSelection={true}
              enableCellTextSelection={true}
            />
          </div>
        )}
      </article>
    </section>
  );
};

export default AboutTarget;
