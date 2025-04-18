export const config = {
	widgetConfig: [
		{
			id: 'rnaseq',
			label: 'Rnaseq Data',
			description_prompt: '{$data}\n',
		},
		{
			id: 'pipeline_indications',
			label: 'Pipeline (by Indications)',
			description_prompt: '{$data}',
		},
		{
			id: 'animal_models',
			label: 'Animal Models',
			description_prompt: '{$data}',
		},
		{
			id: 'literature',
			label: 'Literature',
			description_prompt: '{$data}',
		},
	],
};
