import time
import pandas as pd
from agent import triage_ticket
from pathlib import Path


def process_tickets(input_csv_path: str, output_csv_path: str):

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
        issue = str(row['Issue'])

        subject = str(row.get('Subject', '')) if not pd.isna(row.get('Subject')) else ""
        company = str(row.get('Company', 'None')) if not pd.isna(row.get('Company')) else "None"

        #print(f"Processing ticket {index + 1}/{total_tickets} (Company: {company})...")
        #logging.info(f"Processing row {index}: {issue[:50]}")

        # --- SMART RETRY LOGIC (Handles 429 & 503) ---
        max_retries = 4 
        for attempt in range(max_retries):
            try:
                # Attempt to get the answer
                print(f"Processing ticket {index + 1}/{total_tickets} (Company: {company})...")
                result = triage_ticket(issue, subject, company)

                # If successful, save it!
                statuses.append(result.get('status', 'escalated'))
                request_types.append(result.get('request_type', 'invalid'))
                product_areas.append(result.get('product_area', 'unknown'))
                responses.append(result.get('response', 'System Error - Check Logs'))
                justifications.append(result.get('justification', 'Failed to parse response'))
                
                # Base delay to not trigger rate limits normally
                time.sleep(4) 
                break # Break out of the retry loop because it worked!

            except Exception as e:
                error_msg = str(e).lower()
                
                # Catch both Rate Limits (429) and Server Overloads (503)
               # Catch both Rate Limits (429) and Server Overloads (503)
                if "429" in error_msg or "quota" in error_msg or "503" in error_msg or "unavailable" in error_msg:
                    wait_time = (2 ** attempt) * 10
                    
                    # --- THE FIX: PRINT THE RAW ERROR ---
                    print(f"   [!] EXACT ERROR CAUSING RETRY: {e}")
                    print(f"   [!] Pausing for {wait_time} seconds before retry...")
                    # ------------------------------------
                    
                    time.sleep(wait_time)
        else:
            # SAFETY NET: If it tried 4 times and failed every time
            print(f"   [X] Failed to process ticket {index + 1} after {max_retries} attempts. Skipping.")
            
            # Append failure data so the columns don't get misaligned
            statuses.append('escalated')
            request_types.append('invalid')
            product_areas.append('unknown')
            responses.append('System Error - Max Retries Exceeded')
            justifications.append('API Timeout/Overload')

    print(f"\nFinished processing {total_tickets} tickets.")

    df['status'] = statuses
    df['request_type'] = request_types
    df['product_area'] = product_areas
    df['response'] = responses
    df['justification'] = justifications

    Path(output_csv_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv_path, index=False)
    
    print(f"Success! Results saved to {output_csv_path}")

if __name__ == "__main__":
    INPUT_FILE = "support_tickets/support_tickets.csv"
    OUTPUT_FILE = "support_tickets/output.csv"
    
    process_tickets(INPUT_FILE, OUTPUT_FILE)