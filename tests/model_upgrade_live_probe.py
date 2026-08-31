"""Opt-in paid three-disease and conversational smoke checks, no private inputs."""
import asyncio
import json
import time
from backend.services.research_chat import ResearchRequest, research_events

async def check(question, history=None):
    start = time.monotonic()
    async for event in research_events(ResearchRequest(question=question, history=history or []), {}):
        if event["type"] == "answer":
            data = event["data"]
            print(json.dumps({"question": question, "seconds": round(time.monotonic()-start, 1),
                              "model": data["model"], "sources": len(data["sources"]),
                              "publishers": [s["title"] for s in data["sources"]],
                              "answer": data["answer"]}), flush=True)
            assert data["sources"], "Grounding unavailable"
            return data["answer"]

async def main():
    answer = await check("Explain briefly why measles outbreaks can occur despite high national vaccination coverage. Use official sources.")
    await check("How does that affect infants? Keep it brief.", [{"question": "Why can measles outbreaks occur despite high vaccination coverage?", "answer": answer}])
    await check("Give a concise Ebola outbreak brief explaining transmission and WHO recommended control measures. Do not invent current case counts.")
    await check("Give a concise cholera outbreak brief explaining who is vulnerable and WHO recommended prevention measures. Do not invent current case counts.")

if __name__ == "__main__":
    asyncio.run(main())
