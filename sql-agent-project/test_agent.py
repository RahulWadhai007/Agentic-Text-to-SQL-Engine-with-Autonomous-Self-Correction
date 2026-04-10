# test_agent.py
from app.agent import run_agent

def main():
    print("--- INITIATING AI AGENT TEST ---")
    
    # A complex question requiring a 3-way JOIN and a WHERE clause.
    # This is designed to test the self-correction loop.
question = "Can you give me the names of customers who returned a product, and sort them by the 'return_reason' column?"
    
print(f"User Question: '{question}'\n")
print("Starting LangGraph execution loop...\n")
    
    # Trigger the agent
final_state = run_agent(question, thread_id="test_thread_001", role="admin")
    
print("\n==========================================")
print("--- FINAL AGENT STATE ---")
print(f"Total Execution Attempts: {final_state.get('retry_count', 0) + 1}")
    
if final_state.get('error_message'):
        print(f"Status: FAILED (Max retries reached)")
        print(f"Last Error: {final_state.get('error_message')}")
else:
        print("Status: SUCCESS")
        print(f"Final SQL Query Executed:\n{final_state.get('sql_query')}\n")
        print("Extracted Data:")
        for row in final_state.get('final_result', []):
            print(f" - {row}")
print("==========================================\n")

if __name__ == "__main__":
    main()