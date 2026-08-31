"""Opt-in Vertex AI conversation check, excluded from the ordinary test suite."""
import asyncio
import time
from backend.services.research_chat import ResearchRequest, research_events
from backend.services.science import science_answer

async def main():
    start=time.monotonic()
    request=ResearchRequest(question='Does that apply to measles?', history=[{'question':'what is heard immunity?', 'answer':science_answer('what is herd immunity?')}])
    async for event in research_events(request, {}):
        if event['type']=='answer':
            data=event['data']
            print({'seconds':round(time.monotonic()-start,1),'words':len(data['answer'].split()),'sources':len(data['sources']),'answer':data['answer']})
        else:
            print(event,flush=True)

if __name__=='__main__':
    asyncio.run(main())
