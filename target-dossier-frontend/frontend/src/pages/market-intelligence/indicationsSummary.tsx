import React, { useMemo } from "react";
import Table from "../../components/testTable";

type TrialData = {
  Target: string;
  OutcomeStatus: "Success" | "Failed" | "Indeterminate" | "Not Known";
  Disease: string;
  ApprovalStatus: string;
};

type ResultData = {
  Target: string;
  successfulDiseaseCount: number;
  failedTrialsDiseaseCount: number;
  indeterminateTrialsDiseaseCount: number;
  notKnownDiseaseCount: number;
  approvedDrugDiseaseCount: number;
};

const generateTargetSummary = (data: TrialData[]): ResultData[] => {
  const summaryMap: Record<string, ResultData> = {};
  const successDiseaseMap: Record<string, Set<string>> = {};
  const failedDiseaseMap: Record<string, Set<string>> = {};
  const indeterminateDiseaseMap: Record<string, Set<string>> = {};
  const notKnownDiseaseMap: Record<string, Set<string>> = {};
  const approvedDrugDiseaseMap: Record<string, Set<string>> = {};

  data.forEach((trial) => {
    const { Target, OutcomeStatus, Disease, ApprovalStatus } = trial;

    // Initialize the target if not already present
    if (!summaryMap[Target]) {
      summaryMap[Target] = {
        Target,
        successfulDiseaseCount: 0,
        failedTrialsDiseaseCount: 0,
        indeterminateTrialsDiseaseCount: 0,
        notKnownDiseaseCount: 0,
        approvedDrugDiseaseCount: 0,
      };
      successDiseaseMap[Target] = new Set<string>();
      failedDiseaseMap[Target] = new Set<string>();
      indeterminateDiseaseMap[Target] = new Set<string>();
      notKnownDiseaseMap[Target] = new Set<string>();
      approvedDrugDiseaseMap[Target] = new Set<string>();
    }

    if (ApprovalStatus === "Approved") {
      approvedDrugDiseaseMap[Target].add(Disease); // Add Disease to approved drug map
    }

    // Increment counts based on OutcomeStatus
    if (OutcomeStatus === "Success") {
      successDiseaseMap[Target].add(Disease); // Add Disease to success map
    } else if (OutcomeStatus === "Failed") {
      failedDiseaseMap[Target].add(Disease); // Add Disease to failed map
    } else if (OutcomeStatus === "Indeterminate") {
      indeterminateDiseaseMap[Target].add(Disease); // Add Disease to indeterminate map
    } else if (OutcomeStatus === "Not Known") {
      notKnownDiseaseMap[Target].add(Disease); // Add Disease to not known map
    }
  });

  Object.keys(summaryMap).forEach((target) => {
    summaryMap[target].successfulDiseaseCount = successDiseaseMap[target].size;
    summaryMap[target].failedTrialsDiseaseCount = failedDiseaseMap[target].size;
    summaryMap[target].indeterminateTrialsDiseaseCount = indeterminateDiseaseMap[target].size;
    summaryMap[target].notKnownDiseaseCount = notKnownDiseaseMap[target].size;
    summaryMap[target].approvedDrugDiseaseCount = approvedDrugDiseaseMap[target].size;
  });

  return Object.values(summaryMap);
};

type IndicationsSummaryProps = {
  indicationData: TrialData[];
};

const IndicationsSummary: React.FC<IndicationsSummaryProps> = ({ indicationData }) => {
  const summaryData = useMemo(() => generateTargetSummary(indicationData), [indicationData]);

  return (
    <div className="mb-10">
      <h2 className="text-xl subHeading font-semibold mb-3 mt-4">
        Summary of Targets by Outcome
      </h2>
      <p className="mt-2 font-medium">Summary of targets with the number of indications for which they are approved or in clinical trials.</p>
      {summaryData && (
        <div className="ag-theme-quartz mt-4">
          <Table
            columnDefs={[
              { headerName: "Target", field: "Target" },
              { headerName: "Approved Drug", field: "approvedDrugDiseaseCount", sort: "desc" },
              { headerName: "Successful", field: "successfulDiseaseCount" },
              { headerName: "Failed", field: "failedTrialsDiseaseCount" },
              { headerName: "Indeterminate", field: "indeterminateTrialsDiseaseCount" },
              { headerName: "Not Known", field: "notKnownDiseaseCount" },
            ]}
            rowData={summaryData}
            maxRows={summaryData.length > 10 ? 10 : summaryData.length}
          />
        </div>
      )}
    </div>
  );
};

export default IndicationsSummary;
