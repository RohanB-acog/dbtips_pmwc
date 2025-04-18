// Flattens a nested JSON object
export const flattenJson = (y, parentKey = '', sep = '.') => {
	let items = [];
	Object.keys(y).forEach((k) => {
		if (k === '__typename') return;
		const newKey = parentKey ? `${parentKey}${sep}${k}` : k;
		if (typeof y[k] === 'object' && !Array.isArray(y[k]) && y[k] !== null) {
			items = items.concat(Object.entries(flattenJson(y[k], newKey, sep)));
		} else if (Array.isArray(y[k])) {
			y[k].forEach((item, i) => {
				if (typeof item === 'object' && item !== null) {
					items = items.concat(
						Object.entries(flattenJson(item, `${newKey}${sep}${i}`, sep))
					);
				} else {
					items.push([`${newKey}${sep}${i}`, item]);
				}
			});
		} else {
			items.push([newKey, y[k]]);
		}
	});
	return Object.fromEntries(items);
};

const getMatchingKeys = (flatItem, column) => {
	const matchingKeys = Object.keys(flatItem).filter(
		(flatKey) => flatKey.startsWith(`${column}.`) || flatKey === column
	);
	let value = matchingKeys.length ? flatItem[matchingKeys[0]] : '';

	if (typeof value === 'string' && value.includes(',')) {
		value = value.split(',').join('|');
	}

	return value;
};

// converts json to csv
export const jsonToCsv = (
	jsonData,
	columns,
	delimiter = '\t',
	columnMapping = {}
) => {
	if (!jsonData || jsonData.length === 0) {
		return 'No data available';
	}

	// Flatten the JSON data
	const flattenedData = jsonData.map((item) => flattenJson(item));

	// Generate headers
	const headers = columns.map((col) => columnMapping[col] || col);
	const header = headers.join(delimiter);

	// Generate rows
	const rows = flattenedData.map((flatItem) => {
		return columns
			.map((col) => {
				// Ensure getMatchingKeys handles undefined or missing data gracefully
				const value = getMatchingKeys(flatItem, col);
				return value !== undefined ? value : ''; // Default to empty string if no value
			})
			.join(delimiter); // Use the passed delimiter here
	});

	// Combine headers and rows
	const csvData = [header, ...rows].join('\n');
	return csvData;
};

export const preprocessTargetData = (data) => {
	const columns = [
		'Drug',
		'Drug URL',
		'Type',
		'Mechanism of Action',
		'Disease',
		'Disease URL',
		'Phase',
		'Status',
		'Trial Ids',
		'Sponsor',
	];

	const escapeCsvField = (field) => {
		if (field) {
			return `"${field.replace(/"/g, '""')}"`;
		}
		return '';
	};

	// CSV transformation logic
	const jsonToCsv = (jsonData, columns, delimiter = ',') => {
		if (!jsonData || jsonData.length === 0) {
			return 'No data available';
		}

		const rows = jsonData.map((entry) => {
			return [
				escapeCsvField(entry['Drug'] || ''),
				escapeCsvField(entry['Drug URL'] || ''),
				escapeCsvField(entry['Type'] || ''),
				escapeCsvField(entry['Mechanism of Action'] || ''),
				escapeCsvField(entry['Disease'] || ''),
				escapeCsvField(entry['Disease URL'] || ''),
				entry['Phase'] || '',
				escapeCsvField(entry['Status'] || ''),
				escapeCsvField(entry['Source URLs']?.join(' | ') || ''),
				escapeCsvField(entry['Sponsor'] || ''),
			].join(delimiter);
		});

		return [columns.join(delimiter), ...rows].join('\n');
	};

	const csvData = jsonToCsv(data, columns, ',');

	// console.log('Processed Target CSV:', csvData);

	return csvData;
};

export const preprocessLiteratureData = (data) => {
	const columns = [
		'Disease',
		'PubMedLink',
		'PublicationType',
		'Qualifers',
		'Title',
		'Year',
	];

	const escapeCsvField = (field) => {
		if (field) {
			return `"${field.replace(/"/g, '""')}"`;
		}
		return '';
	};

	const jsonToCsv = (jsonData, columns, delimiter = ',') => {
		if (!jsonData || jsonData.length === 0) {
			return 'No data available';
		}

		const rows = jsonData.map((entry) => {
			const { Disease, PubMedLink, PublicationType, Qualifers, Title, Year } =
				entry;

			return [
				escapeCsvField(Disease || ''),
				escapeCsvField(PubMedLink || ''),
				escapeCsvField(PublicationType?.join(' | ') || ''),
				escapeCsvField(Qualifers?.join(' | ') || ''),
				escapeCsvField(Title || ''),
				Year || '',
			].join(delimiter);
		});

		return [columns.join(delimiter), ...rows].join('\n');
	};

	const csvData = jsonToCsv(data, columns, ',');

	// console.log('Processed Literature CSV:', csvData);

	return csvData;
};

// export const preprocessAnimalmodelData = (data) => {
// 	// console.log(data);
// 	const columns = [
// 		'Model',
// 		'Gene',
// 		'Species',
// 		'ExperimentalCondition',
// 		'Association',
// 		'Evidence',
// 		'References',
// 	];
// 	const columnMapping = {
// 		Model: 'Model',
// 		Gene: 'GenePerturbed',
// 		Species: 'Species',
// 		ExperimentalCondition: 'ExperimentalCondition',
// 		Association: 'Association',
// 		Evidence: 'Evidence',
// 		References: 'References',
// 	};
// 	// console.log(jsonToCsv(data, columns));
// 	// return jsonToCsv(data, columns, columnMapping);
// };

export const preprocessRnaseqData = (data) => {
	// const data = [
	// 	{
	// 		GseID: 'GSE247047',
	// 		Title: [
	// 			'Single cell sequencing delineates T-cell clonality and pathogenesis of the parapsoriasis disease group',
	// 		],
	// 		Platform: {
	// 			PlatformName: 'GPL24676',
	// 			Description: 'Illumina NovaSeq 6000 (Homo sapiens)',
	// 		},
	// 		Design: [
	// 			'Comparison of skin cells obtained from AD, PP, and MF patients.',
	// 			'Healthy control samples from trunk area.',
	// 		],
	// 		Organism: ['Homo sapiens'],
	// 		Samples: [
	// 			{
	// 				SampleID: 'GSM7882574',
	// 				TissueType: 'Skin Biopsy',
	// 				Characteristics: ['tissue: Skin Biopsy', 'subject id: 115 – HC2'],
	// 			},
	// 			{
	// 				SampleID: 'GSM7882575',
	// 				TissueType: 'Skin Biopsy',
	// 				Characteristics: ['tissue: Skin Biopsy', 'subject id: 116 – HC3'],
	// 			},
	// 		],
	// 	},
	// ];
	console.log('rnaseq llm data', data);
	const columns = [
		'GseID',
		'Title',
		'Platform',
		'Design',
		'Organism',
		'StudyType',
		'SampleID',
		'TissueType',
		'Characteristics',
	];
	const jsonToCsv = (jsonData, columns, delimiter = ',') => {
		if (!jsonData || jsonData.length === 0) {
			return 'No data available';
		}
		const escapeCsvField = (field) => {
			if (field) {
				// Ensure double quotes around fields with commas or special characters
				return `"${field.replace(/"/g, '""')}"`;
			}
			return '';
		};
		const rows = jsonData.flatMap((entry) => {
			const { GseID, Title, Platform, Design, Organism, StudyType, Samples } =
				entry;
			return Samples.map((sample) => {
				const { SampleID, TissueType, Characteristics } = sample;
				return [
					GseID || '',
					escapeCsvField(Title?.join(' | ') || ''),
					escapeCsvField(
						Object.entries(Platform || {})
							.map(([key, value]) => `${key}: ${value}`)
							.join(' | ') || ''
					),
					escapeCsvField(Design?.join(' | ') || ''),
					escapeCsvField(Organism?.join(', ') || ''),
					StudyType || '',
					SampleID || '',
					escapeCsvField(TissueType || ''),
					escapeCsvField(Characteristics?.join(' | ') || ''),
				].join(delimiter);
			});
		});
		return [columns.join(delimiter), ...rows].join('\n');
	};
	let answer = jsonToCsv(data, columns, ',');
	console.log(answer);
	return answer;
};
