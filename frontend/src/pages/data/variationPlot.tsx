import { useState, useEffect } from "react";
import Plotly from "plotly.js-dist-min";
import LocusZoom from "locuszoom";
import { Select, message, Empty } from "antd";
import { useQuery } from "react-query";
import { fetchData } from "../../utils/fetchData"; // assuming fetchData is a utility function to fetch data
import LoadingButton from "../../components/loading";
import CHROMOSOMES from "./chromosomes.json";

const { Option } = Select;

function DiseasePlot({ diseases }) {
  const [selectedDisease, setSelectedDisease] = useState("");
  const [allPoints, setAllPoints] = useState([]);
  const [mondoId, setMondoId] = useState(null);

  // Reset data on disease change
  useEffect(() => {
    setAllPoints([]);
    setMondoId(null); // Reset mondoId when disease changes
  }, [selectedDisease]);

  const handleDiseaseChange = (value) => {
    setSelectedDisease(value);
  };

  // Payload for LocusZoom query based on selected disease
  const payload = { disease: selectedDisease };

  const { data: locuszoomData, error: locuszoomError, isLoading: locuszoomLoading } = useQuery(
    ["locuszoom", payload],
    () => fetchData(payload, "/genomics/locus-zoom"),
    {
      enabled: selectedDisease !== "", // Only run query if a disease is selected
      refetchOnWindowFocus: false,
			staleTime: 5 * 60 * 1000,
			refetchOnMount: false,
		
    }
  );

  useEffect(() => {
    if (locuszoomData) {
      const id = locuszoomData.split("/").pop();
      setMondoId(id); // Set mondoId once locuszoomData is available
    }
  }, [locuszoomData]);

  useEffect(() => {
    if (!mondoId) return;

    const url = `${import.meta.env.VITE_API_URI}/api/download/${mondoId}`;

    fetch(url)
      .then((response) => response.text())
      .then((text) => {
        processFileData(text); // Process the TSV data for the plot
      })
      .catch((error) => {
        message.error("Error fetching data for the disease.");
        console.error("Error fetching TSV:", error);
      });
  }, [mondoId]);

  const processFileData = (data) => {
    const rows = data.split("\n").map((row) => row.split("\t"));
    const headers = rows.shift();
    const chrIndex = headers.indexOf("Chromosome");
    const posIndex = headers.indexOf("Position");
    const pvalIndex = headers.indexOf("pvalue");
    const rsidIndex = headers.indexOf("rsID");
    const refAlleleIndex = headers.indexOf("Variant and Risk Allele");
    const authorIndex = headers.indexOf("Author");
    const pubmedidIndex = headers.indexOf("PubMed ID");
    const mappedgeneIndex = headers.indexOf("Mapped gene(s)");
    const reportedtraitIndex = headers.indexOf("Reported trait");

    if (
      [chrIndex, posIndex, pvalIndex, rsidIndex, refAlleleIndex, authorIndex, pubmedidIndex].includes(
        -1
      )
    ) {
      message.error("Required columns not found in TSV file.");
      return;
    }

    const dataMap = {};
    const allPointsArray = [];

    rows.forEach((row) => {
      if (row.length < headers.length) return;
      const chr = row[chrIndex];
      const pos = parseInt(row[posIndex]);
      const pval = parseFloat(row[pvalIndex]);
      const rsID = row[rsidIndex];
      const logPval = -Math.log10(pval);
      const author = row[authorIndex];
      const pubmedid = row[pubmedidIndex];
      const refallele = row[refAlleleIndex];
      const mappedgene = row[mappedgeneIndex];
      const reportedtrait = row[reportedtraitIndex];
      if (!dataMap[chr]) dataMap[chr] = { x: [], y: [], text: [], positions: [], locusX: [] };
      const chromosome = CHROMOSOMES.chromosomes.find((c) => c.name === (chr));
      const location = chromosome ? parseFloat(chromosome?.location.toString()) : 0; // Default to 0 if not found
      
      // Calculate x as location + position
      const xValue = location + pos;
      
      dataMap[chr].x.push(xValue);
      dataMap[chr].y.push(logPval);
      dataMap[chr].locusX.push(chr);
      dataMap[chr].text.push(
        `rsID: ${rsID}<br>Chromosome: ${chr}<br>P-value: ${pval}<br>Reference Allele: ${refallele}<br>Mapped Gene(s): ${mappedgene}<br>Reported Trait: ${reportedtrait}<br>Author: ${author}<br>PubMed ID: ${pubmedid}`
      );
      dataMap[chr].positions.push(pos);

      allPointsArray.push({ chr, pos, rsID, author, pubmedid, logPval });
    });

    setAllPoints(allPointsArray);
    renderManhattanPlot(dataMap);
  };

  useEffect(() => {
    setSelectedDisease(diseases[0]);
  }, [diseases]);

  const renderManhattanPlot = (data) => {
    const plotDiv = document.getElementById("plot");
    Plotly.purge(plotDiv); // Clear the existing plot before rendering the new one
    const traces: Partial<Plotly.Data>[] = Object.keys(data).map((chr) => ({
      x: data[chr].x,
      y: data[chr].y,
      mode: "markers",
      type: "scatter",
      name: `Chr ${chr}`,
      text: data[chr].text,
      hoverinfo: "text",
      marker: { size: 5 },
      customdata: data[chr].positions,
      locusX: data[chr].locusX,
    }));

    const layout = {
      title: {
        text: "Manhattan Plot with Variant Details",
      },
      xaxis: {
        title: {
          text: "Chromosome",
        },
        tickvals: CHROMOSOMES.chromosomes.map((d) => d.location + d.length / 2)        ,
        ticktext: CHROMOSOMES.chromosomes.map((d) => d.name),
      },
      shapes: [
        {
          type: 'line',
          x0: 0,  // Starting x position
          x1: 3199026875,  // Ending x position
          y0: 8,  // y position of the threshold line
          y1: 8,  // y position of the threshold line
          line: {
            color: 'grey',  // Line color
            dash: 'dash',  // Dash style
            width: 2,      // Line width
            length:1
          },
        },
      ],
  
      yaxis: {
        title: {
          text: "-log10(p-value)",
        },
      },
      hovermode: "closest" as const,
      showlegend: false,
    };

    Plotly.newPlot(plotDiv, traces, layout).then((plot) => {
      plot.on("plotly_click", function (data) {
        console.log("plotly_click", data);
        const point = data.points[0];
        console.log("point", point);
        const chr = point.data.locusX[0];
        const pos = point.customdata;
        const rsID =
          allPoints.find((p) => p.chr === chr && p.pos === pos)?.rsID || "Unknown";
        renderLocusZoom(chr, pos, rsID);
      });
    });
  };

  const renderLocusZoom = (chr, pos, rsID) => {
    const apiBase = "https://portaldev.sph.umich.edu/api/v1/";
    const data_sources = new LocusZoom.DataSources()
      .add("assoc", [
        "AssociationLZ",
        {
          url: apiBase + "statistic/single/",
          source: 45,
          id_field: "variant",
        },
      ])
      .add("ld", ["LDServer", { url: "https://portaldev.sph.umich.edu/ld/" }])
      .add("recomb", [
        "RecombLZ",
        { url: apiBase + "annotation/recomb/results/", build: "GRCh37" },
      ])
      .add("gene", [
        "GeneLZ",
        { url: apiBase + "annotation/genes/", build: "GRCh37" },
      ])
      .add("constraint", [
        "GeneConstraintLZ",
        { url: "https://gnomad.broadinstitute.org/api/", build: "GRCh37" },
      ]);

    const layout = LocusZoom.Layouts.get("plot", "standard_association", {
      state: {
        genome_build: "GRCh38",
        chr,
        start: pos - 50000,
        end: pos + 50000,
        highlight: rsID,
      },
      axes: {
        x: {
          label: "Genomic Position",
        },
        y1: {
          label: "-log10(p-value)",
        },
      },
    });
    LocusZoom.populate("#lz-plot", data_sources, layout);
  };

  return (
    <div>
      <h2 className="text-lg subHeading font-semibold mb-3 mt-4">Manhattan Plot</h2>
      <p className="my-1 font-medium">
      A genome-wide visualization of SNP significance, highlighting risk loci in GWAS. Click on a specific variant to view the 'LocusZoom plot'.
      </p>
      <div>
        <span className="mt-10 mr-1">Disease:</span>
        <span>
          <Select
            style={{ width: 250 }}
            placeholder="Select a disease"
            onChange={handleDiseaseChange}
            value={selectedDisease}
            loading={locuszoomLoading}
          >
            {diseases.map((disease) => (
              <Option key={disease} value={disease}>
                {disease}
              </Option>
            ))}
          </Select>
        </span>
      </div>

      {locuszoomLoading && <LoadingButton />}
      {locuszoomError && <Empty description="Failed to load data" />}
      {!locuszoomLoading && !locuszoomError && locuszoomData === null && (
        <div className="h-[40vh] flex justify-center items-center">
          <Empty description="No data available" />
        </div>
      )}
      {!locuszoomLoading && !locuszoomError && locuszoomData !== null && (
        <div>
          <div
            id="plot"
            style={{ width: "100%", height: "400px", marginTop: "20px" }}
          ></div>
          <div id="lz-plot" style={{ marginTop: "20px" }}></div>
        </div>
      )}
    </div>
  );
}

export default DiseasePlot;
