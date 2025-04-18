// import React from 'react';
import { FloatButton } from "antd";
import CoverImage from "../assets/coverLetter.png";
import { useMemo } from "react";
// import OngoingCT from "../assets/ongoingCT.png";
// import PastCT from "../assets/pastCT.png";
// import Pathways from "../assets/pathways.png";
import { useQuery } from "react-query";
import { fetchData } from "../utils/fetchData";
import {   useNavigate } from 'react-router-dom';
import LoadingButton from "../components/loading";

import Table from "../components/testTable"
const indicationsList = [
  "Prurigo nodularis",
  "Alopecia areata",
  "Asthma",
  "Hidradenitis suppurativa",
  "Chronic idiopathic urticaria",
];
const scrollIntoView = (id) => {
  const section = document.getElementById(id);
  const headerOffset = 80; // Height of the sticky header
  const elementPosition = section.getBoundingClientRect().top;
  const offsetPosition = elementPosition + window.scrollY - headerOffset;

  window.scrollTo({
    top: offsetPosition,
    behavior: 'smooth',
  });
};



const statusMap=(value)=>{
  if(value==="Approved") return "4";
  else if(value==="Successful trial") return "3";
  else if(value==="Ongoing trial") return "2";
  else if(value==="Pathway") return "1";
}

function convertToArray(data) {
  const result = [];
  Object.keys(data).forEach((disease) => {
    console.log("disease inside convert array function", disease);
    data[disease].forEach((record) => {
      result.push({
        ...record, // Add the disease key
        Status:statusMap(record["EvidenceType"])
      });
    });
  });
  return result;
}
const CoverLetter = () => {
	const navigate = useNavigate();
  const navigateWithParams = (path, key) => {

    // Join indications with double quotes and commas
    const indications = indicationsList
      .map((indication) => `"${indication}"`)
      .join(',');
  
    // Navigate with target and formatted indications as query params
    navigate(`${path}?indications=${indications}`);
  
    // Scroll into view after navigation
    setTimeout(() => {
      scrollIntoView(key);
    }, 250);
  };
  const payload = { 
    diseases:indicationsList
  }
  const {
    data: indicationData,
    isLoading,
  } = useQuery(
    ["coverLetter", payload],
    () => fetchData(payload, "/target-indication-pairs"),
    {
      enabled: !!indicationsList.length,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
      refetchOnMount: false,
     
    }
  );
  const processedData = useMemo(() => {
    if (indicationData) {
      return convertToArray(indicationData);
    }
    return [];
  },[indicationData]);
  console.log("processedData",processedData); 
 
  return (
    <div className="bg-gray-50 min-h-screen ">
         
      <header className="py-5 max-w-5xl mx-auto   text-black">
        <h1 className="text-5xl ">Cover note for disease dossier</h1>
        <p className="mt-2 text-lg">A comprehensive overview of key objectives and outcomes</p>
      </header>

      <main className="max-w-5xl mx-auto bg-white shadow-lg rounded-lg p-10 mt-1">
        <section className="mb-10">
          <h1 className="text-3xl font-semibold subHeading mb-4">Objectives & context</h1>
          <p className="text-gray-700 mb-6">
            This dossier is delivered from phase 1 of a multi-phase delivery plan to answer the following <b> two key questions</b> posed by Astria.
          </p>
          <ul className="list-disc pl-6 text-gray-700 space-y-4">
            <li>
              <span className="font-semibold">Target identification across 5 indications of interest</span>
              <ul className="list-disc pl-6 space-y-2">
                <li>Analyze respective pathophysiological pathways for five indications of interest.</li>
                <li>Identify and rank targets effective across the greatest number of these indications.</li>
              </ul>
            </li>
            <li>
              <span className="font-semibold">OX40 pathway assessment</span>
              <ul className="list-disc pl-6 space-y-2">
                <li>Evaluate and rank the five indications based on their relationship to the OX40 pathway.</li>
                <li>Determine the potential effectiveness of OX40 inhibition for each indication.</li>
              </ul>
            </li>
          </ul>
        </section>

        <section className="mb-10">
          <h1 className="text-3xl font-semibold subHeading mb-4">Indications under consideration</h1>
          <div className="grid grid-cols-2 gap-4">
            {[
              "Prurigo nodularis",
              "Alopecia areata",
              "Asthma",
              "Hidradenitis suppurativa",
              "Chronic spontaneous urticaria",
            ].map((indication, index) => (
              <div
                key={index}
                className="bg-gray-100 p-4 rounded-lg  "
              >
                <p className="text-gray-800 font-medium">{indication}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mb-10">
          <h1 className="text-3xl font-semibold subHeading mb-4">Additional Astria-specific context</h1>
          <ul className="list-disc pl-6 text-gray-700 space-y-4">
            <li>Experience with antibody modality</li>
            <li>Existing pipeline assets for HAE & AD indications</li>
            <li>Exploring opportunities for bispecifics</li>
          </ul>
        </section>

        <section className="mb-10">
          <h1 className="text-3xl font-semibold subHeading mb-4">Overall plan</h1>
          <img src={CoverImage} alt="Cover Letter Illustration" className="rounded-lg shadow-md mx-auto" />
        </section>

        <section className="mb-10">
          <h1 className="text-3xl font-semibold subHeading mb-4">Guide to using this dossier</h1>
          <p className="text-gray-700 mb-6 font-semibold"> Key sections:</p>
          <ul className="list-disc pl-6 text-gray-700 space-y-4">
            <li>
              <span className="font-semibold cursor-pointer">Clinical evidence in <span onClick={() => navigateWithParams('/market-intelligence','pipeline-by-indications')}
        className="underline "> market intelligence section:</span></span> Availability, clarity and relevance of success/failure data for specific target-indication pairs. Nature & stage of competition. Reasons for termination incl. under-enrollment and adverse events.
            </li>
            <li>
              <span onClick={() => navigateWithParams('/literature', 'knowledge-graph-evidence')}
        className="underline font-semibold cursor-pointer ">Pathway figures under literature section:</span> Look for types of inflammation involved, cell types of relevance, tissues (skin, lung, etc.) involved, itch-scratch or exposure-reaction processes.
            </li>
            <li>
              <span onClick={() => navigateWithParams('/data', 'rnaSeq')}
              className="underline font-semibold cursor-pointer">RNA-seq datasets</span> <span className="font-semibold">relevant to indications of interest: </span>
              <span>Look for datasets from studies on disease tissue in humans for the most relevant insights. Single-cell studies provide more granular insights compared to bulk studies.</span>
            </li>
            <li>
              <span className="font-semibold underline cursor-pointer" onClick={() => navigateWithParams('/model-studies', 'model-studies')}>Animal model studies:</span> <span> Look for the gene perturbed and association type. The phenotype studies can be looked at  by clicking on the “model” column.</span>
            </li>
          </ul>
        </section>
        <section className="mb-10">
        <h1 className="text-3xl font-semibold subHeading mb-4">Ask LLM to take multiple perspectives
          </h1>
          <span className="font-semibold mb-2">Perspectives to take when reviewing the information in this dossier & subsequent phases:
          </span>
          <ul className="list-disc pl-6 text-gray-700 space-y-4">
  <li><span className="font-semibold">Patient outcomes:</span> Efficacy, potency</li>
  <li><span className="font-semibold">Patient experience:</span> Safety, adverse events</li>
  <li><span className="font-semibold">Commercial opportunities/challenges:</span> Nature and stage of competition, synergy (or lack of it) across indications with respect to market access & KOL influence</li>
  <li><span className="font-semibold">Regulatory concerns to expect:</span> Dosages needed for availability & related tox burden</li>
  <li><span className="font-semibold">Science readiness:</span> Data availability, tractability</li>
</ul>
<br />
<span className="mt-4">
To enable the investigation of data in this dossier with these perspectives and more, the dossier is integrated with AI Large Language Models (LLM) such as OpenAI ChatGPT. Currently, this facility is available with the <div className="w-[20px] h-[20px]" style={{display:"inline-block"}}><svg id="Layer_1" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" data-name="Layer 1"><path d="m320.331 328.931a72.563 72.563 0 0 1 -128.659 0 12 12 0 1 1 21.279-11.1 48.561 48.561 0 0 0 86.1 0 12 12 0 1 1 21.283 11.1zm31.629-64.279a17.036 17.036 0 1 1 17.04-17.041 17.05 17.05 0 0 1 -17.043 17.041zm0-58.071a41.036 41.036 0 1 0 41.04 41.03 41.082 41.082 0 0 0 -41.038-41.03zm-191.921 58.071a17.036 17.036 0 1 1 17.029-17.041 17.055 17.055 0 0 1 -17.029 17.041zm0-58.071a41.036 41.036 0 1 0 41.03 41.03 41.084 41.084 0 0 0 -41.03-41.03zm325.132 120.15a19.742 19.742 0 0 1 -19.723 19.729h-7.2v-141.5h7.2a19.743 19.743 0 0 1 19.723 19.729v102.04zm-50.921 36.9v-175.841a42.727 42.727 0 0 0 -42.681-42.669h-271.139a42.727 42.727 0 0 0 -42.681 42.669v175.842a42.725 42.725 0 0 0 42.681 42.668h88.4a12.026 12.026 0 0 1 10.4 6l36.77 63.7 36.78-63.7a12 12 0 0 1 10.392-6h88.4a42.725 42.725 0 0 0 42.681-42.669zm-407.422-36.9v-102.04a19.743 19.743 0 0 1 19.722-19.729h7.2v141.5h-7.2a19.742 19.742 0 0 1 -19.722-19.729zm203.911-277.469a25.261 25.261 0 1 1 25.261 25.259 25.288 25.288 0 0 1 -25.26-25.259zm234.709 131.7h-7.548a66.768 66.768 0 0 0 -66.332-59.842h-123.568v-24.088a49.261 49.261 0 1 0 -24 0v24.088h-123.57a66.761 66.761 0 0 0 -66.33 59.842h-7.55a43.778 43.778 0 0 0 -43.723 43.729v102.04a43.776 43.776 0 0 0 43.723 43.729h7.55a66.761 66.761 0 0 0 66.33 59.84h81.478l43.7 75.7a12 12 0 0 0 20.783 0l43.709-75.7h81.469a66.768 66.768 0 0 0 66.331-59.84h7.547a43.776 43.776 0 0 0 43.723-43.729v-102.04a43.777 43.777 0 0 0 -43.722-43.729z" fill="#0b427e" fill-rule="evenodd"/></svg> </div> in the <span className=" underline cursor-pointer" onClick={() => navigateWithParams('/market-intelligence','approvedDrug')}>clinical trials</span> and {" "} 
<span className=" underline cursor-pointer" onClick={() => navigateWithParams('/data', 'rnaSeq')}>RNA-seq </span> datasets related sections.
</span>


        </section>

        <section className="mb-10">
          <h1 className="text-3xl font-semibold subHeading mb-4">Key outcomes from this phase</h1>
          <p>The below table lists target-indication pairs shortlisted for Phase II of the project. Targets listed below have been filtered on the basis of finding evidence supported by implication in at least 2 indications. <br></br>
<span className="font-semibold">Evidence types are as follows:</span> Approved, Successful trial, Ongoing trial, Pathway</p>
          {isLoading && <LoadingButton/>}
         {processedData.length &&
         <Table rowData={processedData} columnDefs={ [
          {field:"Disease"},
          {field:"Target"},
      
          {field:"EvidenceType",headerName:"Evidence Type", 
            sortable:true,
           comparator: (valueA, valueB) => {
            const mappedA = parseInt(statusMap(valueA), 10);
            const mappedB = parseInt(statusMap(valueB), 10);
      
            return mappedA - mappedB; // Sorting logic
        },
       sort:"desc"
        
      },
          {field:"Modality"}
        ]} />
          }
        </section>
        <section className="mb-10">
          <h2 className="text-3xl font-semibold subHeading mb-4">What&rsquo;s Coming Next?</h2>
          <ul className="list-disc pl-6 text-gray-700 space-y-4">
            <li>
              Target dossier to interrogate the targets obtained from the disease dossier, providing further insights on target biology, structural biology, targetability, etc.
            </li>
            <li>
              Enhancing the existing task LLM capability to deeply interrogate existing disease and target dossiers. Ask questions to further investigate the data on the perspectives mentioned above.
            </li>
            <li>
              Transcriptomic data analysis (single cell; phase III deliverable) has been initiated for the indications.
              <ul className="list-disc pl-6 space-y-2">
                <li>Total number of single cell studies is 84</li>
                <li>Runs completed for 3 out of 8 studies for HS</li>
                <li>11 runs are scheduled for CSU, PN, AA</li>

              </ul>

            </li>
            
          </ul>
        </section>
        <section>
        Depending on the pace of progress in analyzing transcriptomic data, we may reprioritize phase III and phase IV.
        </section>
      </main>
      

      <FloatButton
        description="Navigate to dossier"
        type="primary"
        shape="square"
        style={{ width: "200px" }}
        className="fixed bottom-5 right-5 shadow-lg"
        onClick={() => navigate('/home')}
      />
    </div>
  );
};

export default CoverLetter;
