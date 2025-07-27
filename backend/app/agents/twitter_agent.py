from app.services.twitter_service import TwitterCivicAgent
from app.utils.gemini import generate_response
from app.utils.prompt import twitter_prompt

async def run_twitter_to_summary() -> str:
    agent = TwitterCivicAgent()

    # Use a broad query like "issue" or "problem"
    df = agent.fetch_and_process(query="issue OR problem", issue_type="civic", save=False)

    if df is None or df.empty:
        return "No recent civic issue tweets found for Bengaluru."

    # Join tweet texts into a single string for summarization
    all_text = "\n".join(df["text"].dropna().tolist())

    summary = generate_response(twitter_prompt,all_text)
    return summary
