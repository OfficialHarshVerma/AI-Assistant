from langchain_community.tools import DuckDuckGoSearchRun
from tavily import TavilyClient

ddg = DuckDuckGoSearchRun()
tc = TavilyClient()

def search(question):
    for i in range(2):
        try:
            result = ddg.invoke(question)
            return result
        except Exception as e:
            print(f"DuckDuckGo attempt {i + 1} failed: {e}")
    try:
        response = tc.search(
            query=question,
            search_depth="basic",
            max_results=2
            )

        result = response.get("results",[])

        if result:
            print("Search Successful : Tavily")

        return "\n\n".join(
            item.get("content", "")
            for item in result
            if item.get("content")
        )

    except Exception as e:
        print(f"Tavily search failed: {e}")
        print("Web search is currenly unavailable")
