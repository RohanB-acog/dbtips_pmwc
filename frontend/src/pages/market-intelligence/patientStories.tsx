import { useState, useEffect } from "react";
import Papa from "papaparse";
import parse from "html-react-parser";
import { Select } from "antd"; // Import Select from Ant Design
const { Option } = Select;
import Table from "../../components/testTable";
import LoadingButton from "../../components/loading";
const separateByPipeline = ({ value }) => {
  return value
    ?.replace(/[\[\]']/g, "")
    ?.split(", ")
    ?.join("|");
};
const parseDate = (dateString) => {
  const [month, day, year] = dateString.split('/');
  const fullYear = year.length === 2 ? '20' + year : year;
  return new Date(fullYear, month - 1, day);
};


const formatDate = (date) => {
  const day = date.getDate().toString().padStart(2, '0');
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
};

const PatientStories = ({ indications }) => {
  const [csvData, setCsvData] = useState([]);
  const [filteredData, setFilteredData] = useState([]); // Store filtered data
  const [loading,isLoading] = useState(false);
  const [selectedDiseases, setSelectedDiseases] = useState(indications); // Use plural for selected diseases
useEffect(() => {
    setSelectedDiseases(indications);
    }
    , [indications]);
  // Function to fetch the CSV file based on the selected disease
  const fetchCsvData = (filePath) => {
    isLoading(true);
    fetch(filePath)
      .then((response) => response.text()) // Read as text
      .then((text) => {
        // Parse CSV data
        Papa.parse(text, {
          complete: (result) => {
            setCsvData((prevData) => [...prevData, ...result.data]); // Append new data to existing data
            setFilteredData((prevData) => [...prevData, ...result.data]); // Also update filtered data with new data
          },
          header: true, // If your CSV has a header row
        });
      })
      .catch((error) => {
        console.error("Error fetching the CSV file:", error);
      }).finally(()=>{
        isLoading(false);
      }
        );
  };

  useEffect(() => {
    // Clear previous data before fetching new CSV files
    setCsvData([]);
    setFilteredData([]);

    if (selectedDiseases.length > 0) {
      // If "All" is selected, fetch both files
      if (selectedDiseases.includes("All")) {
        if (indications.includes("Friedreich ataxia")) {
          fetchCsvData("/Friedreich%20ataxia.csv");
        }
        if (indications.includes("dermatitis, atopic")) {
          fetchCsvData("/Atopic%20dermatitis.csv");
        }
        if (indications.includes("migraine disorder")) {
          fetchCsvData("/Migraine%20disorder.csv");
        }
      } else {
        // Fetch only the selected disease's CSV file, if it exists in the indications array
        selectedDiseases.forEach((disease) => {
          if (disease === "Friedreich ataxia" && indications.includes("Friedreich ataxia")) {
            fetchCsvData("/Friedreich%20ataxia.csv");
          } else if (disease === "dermatitis, atopic" && indications.includes("dermatitis, atopic")) {
            fetchCsvData("/Atopic%20dermatitis.csv");
          }
          else if (disease === "migraine disorder" && indications.includes("migraine disorder")) {
            console.log("fetching data for migraine disorder");
            fetchCsvData("/Migraine%20disorder.csv");
          }
        });
      }
    }
  }, [selectedDiseases, indications]); // Fetch new data whenever the disease selection changes or indications change

  // Function to handle disease selection
  const handleDiseaseChange = (value) => {
    if (value.includes("All")) {
      // If "All" is selected, select all diseases but don't include "All" in display
      setSelectedDiseases(indications);
    } else if (
      selectedDiseases.length === indications.length &&
      value.length < indications.length
    ) {
      // If coming from "all selected" state and deselecting, just use the new selection
      setSelectedDiseases(value);
    } else {
      // Normal selection behavior
      setSelectedDiseases(value);
    }
  };
  return (
    <div className="px-[5vw] py-16 bg-gray-50" id="patientStories">
      <h1 className="text-xl subHeading font-semibold mb-5">Patient stories</h1>

      {/* Disease selection dropdown */}
      <div className="my-2">
        <span className="mt-10 mr-1">Disease:</span>
        <Select
          mode="multiple"
          allowClear
          style={{ width: 500 }}
          placeholder="Select Diseases"
          maxTagCount="responsive"
                    onChange={handleDiseaseChange}
          value={selectedDiseases} // Set value to selectedDiseases
        >
          <Option value="All">All</Option>
          {indications?.map((disease, index) => (
            <Option key={index} value={disease}>
              {disease}
            </Option>
          ))}
        </Select>
      </div>
          {
        loading && <LoadingButton />
          }
     { csvData && filteredData && !loading && <div className=" ">
        <Table
          rowData={filteredData}
         
          columnDefs={[
            {
              field: "Disease",
              headerName: "Disease",
              flex: 2,
            },
            {
              field: "Video title",
              headerName: "Video Title",
              cellRenderer: (params) => {
                return parse(params.value);
              },
              minWidth: 300,
            },
            {
              field: "Name",
              headerName: "Name",
            },
            {
              field: "Age at video publication",
              headerName: "Age",
              maxWidth: 100,
            },
            {
              field: "Location",
              headerName: "Location",
            },
            {
              field: "Symptoms",
              headerName: "Symptoms",
              cellRenderer: separateByPipeline,
            },
            {
              field: "Medical history of patient",
              headerName: "Medical History",
              cellRenderer: separateByPipeline,
            },
            {
              field: "Family medical history",
              cellRenderer: separateByPipeline,
            },
            {
              field: "Challenges faced during diagnosis",
              headerName: "Challenges Faced During Diagnosis",
              cellRenderer: separateByPipeline,
            },
            {
              field: "Duration minutes",
              headerName: "Duration (in mins)",
              valueGetter: (params) => {
                if (!params.data["Duration minutes"]) return '';  // Ensure the field exists
                
                const timeStr = params.data["Duration minutes"];
                let [minutes, seconds] = timeStr.split('.').map(Number);
                
                // Adjust if seconds are greater than or equal to 60
                if (seconds >= 60) {
                  minutes += Math.floor(seconds / 60);  // Add full minutes
                  seconds = seconds % 60;  // Get the remaining seconds
                }
                
                // Return the adjusted time as a string in the format "minutes.seconds"
                return `${minutes}.${seconds}`;
              }
            },
            
            {
              field: "Published date",
              filter: "agDateColumnFilter",
              filterParams: {
                comparator: (filterLocalDateAtMidnight, cellValue) => {
                  if (!cellValue) return -1;
                  const cellDate = parseDate(cellValue);
                  if (cellDate < filterLocalDateAtMidnight) return -1;
                  else if (cellDate > filterLocalDateAtMidnight) return 1;
                  else return 0;
                },
                browserDatePicker: true
              },
              valueFormatter: (params) => {
                if (!params.value) return '';
                const date = parseDate(params.value);
                return formatDate(date); // Will show as DD/MM/YYYY
              }
            },
            {
              field: "Number of views",
            },
            {
              field: "Sex",
              maxWidth: 100,
            },
          ]}
         
        />
      </div>}
    
    </div>
  );
};

export default PatientStories;
