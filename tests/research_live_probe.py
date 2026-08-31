"""Opt-in public-query smoke check. Does not run with the unit suite."""
import asyncio
import json
from backend.services.research_chat import ResearchRequest, research_events

async def main():
    request = ResearchRequest(question="What are the current major global public-health threats? Give a short dated overview using WHO and CDC sources, not only measles, Ebola and cholera.")
    async for event in research_events(request, {}):
        if event['type'] == 'answer':
            data = event['data']
            print(json.dumps({k:v for k,v in data.items() if k != 'suggestions'}, ensure_ascii=True))
        else:
            print(event, flush=True)

if __name__ == '__main__':
    asyncio.run(main())
