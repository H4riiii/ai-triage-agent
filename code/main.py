import pandas as pd
import logging 
from agent import triage_ticket
from pathlib import Path

logging.basicConfig(
    filename='log.txt',
    level=logging.INFO,
    format = '%(asctime)s - MAIN - %(message)s'
)

def process_tickets(input_csv_path: str, output_csv_path: str):

    logging.info(f"Starting batch processing from {input_csv_path}")
    print(f"Loading {input_csv_path}...")

    if not Path(input_csv_path).exists():
        print(f"Error: Could not find {input_csv_path}.")
        print("Please make sure you are running this from the parent directory.")
        return
    
    df = pd.read_csv(input_csv_path)

    statuses=[]
    request_types=[]
    product_areas=[]
    responses=[]
    justifications=[]

    total_tickets = len(df)

    for index, row in df.iterrows():
        issue = str(row['issue'])

        subject = str(row.get('subject', '')) if not pd.isna(row.get('subject')) else ""
        company = str(row.get('company', 'None')) if not pd.isna(row.get('company')) else "None"

        print(f"Processing ticket{index + 1}/{total_tickets} (Company: {company})...", end = "\r")
        logging.info(f"Processing row {index}: {issue[:50]}")

        result = triage_ticket(issue, subject, company)

        statuses.append(result.get('status', 'escalated'))
        request_types.append(result.get('request_type', 'invalid'))
        product_areas.append(result.get('product_area', 'unknown'))
        responses.append(result.get('response', 'System Error - Check Logs'))
        justifications.append(result.get('justification', 'Failed to parse response'))
    print(f"\nFinished processing {total_tickets} tickets.")
    logging.info("Finished processing all tickets.")

    df['status'] = statuses
    df['request_type'] = request_types
    df['product_area'] = product_areas
    df['response'] = responses
    df['justification'] = justifications

    Path(output_csv_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv_path, index=False)
    
    print(f"Success! Results saved to {output_csv_path}")
    logging.info(f"Results successfully saved to {output_csv_path}")

if __name__ == "__main__":
    INPUT_FILE = "support_tickets/sample_support_tickets.csv"
    OUTPUT_FILE = "support_tickets/output.csv"
    
    process_tickets(INPUT_FILE, OUTPUT_FILE)