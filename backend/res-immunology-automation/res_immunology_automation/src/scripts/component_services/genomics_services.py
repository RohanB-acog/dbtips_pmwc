import requests
from datetime import datetime
import json

def fetch_pgs_data(trait_id):
    try:
        # API endpoint
        base_url = "https://www.pgscatalog.org/rest/score/search"
        params = {'trait_id': trait_id}

        # Make the API request
        response = requests.get(base_url, params=params)
        
        # Check if the response is successful
        if response.status_code == 200:
            data = response.json()
        else:
            print(f"Error: Unable to fetch data (Status Code: {response.status_code})")
            return []

        output = []
        # keys = ['results', 'id', 'name', 'publication', 'trait_reported', 'variants_number', 'ftp_scoring_file', 'ancestry_distribution']
        # publication_keys = ['id', 'firstauthor', 'journal', 'date_publication']
        for result in data.get('results', []):
            if result:
                pgs_id = result.get('id', '')
                pgs_name = result.get('name', '')
                pgs_publication = result.get('publication', {})
                pgs_publication_id = pgs_publication.get('id', '')
                pgs_publication_first_author = pgs_publication.get('firstauthor', '')
                pgs_publication_journal = pgs_publication.get('journal', '')
                pgs_publication_year = datetime.strptime(pgs_publication.get('date_publication', '1900-01-01'), '%Y-%m-%d').year
                pgs_reported_trait = result.get('trait_reported', '')
                pgs_number_of_variants = result.get('variants_number', 0)
                pgs_scoring_file = result.get('ftp_scoring_file', '')
                pgs_ancestry_distribution = result.get('ancestry_distribution', {})
            else:
                continue
            output.append({
                'PGS ID': pgs_id,
                'PGS Name': pgs_name,
                'PGS Publication ID': pgs_publication_id,
                'PGS Publication First Author': pgs_publication_first_author,
                'PGS Publication Journal': pgs_publication_journal,
                'PGS Publication Year': pgs_publication_year,
                'PGS Reported Trait': pgs_reported_trait,
                'PGS Number of Variants': pgs_number_of_variants,
                'PGS Scoring File': pgs_scoring_file,
                'PGS Ancestry Distribution': pgs_ancestry_distribution
            })
    except Exception as e:
        raise e
    return output

if __name__ == "__main__":
    # Fetch and print the data
    pgs_data = fetch_pgs_data("MONDO_0004979")
    print (len(pgs_data))
    for entry in pgs_data:
        print(json.dumps(entry, indent=2))
