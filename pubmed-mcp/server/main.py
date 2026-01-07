from fastmcp import FastMCP
from langchain_community.retrievers import PubMedRetriever
 
mcp = FastMCP("pubmed_mcp_server")
 

@mcp.tool()
def get_pubmed_data(user_question: str) -> dict:
    retriever = PubMedRetriever(top_k_results=4, load_max_docs=4)
    docs = retriever.invoke(user_question)
   
    items = []
    for d in docs or []:
        md = d.metadata or {}
        items.append({
            "uid": md.get("uid") or md.get("Id") or "NA",
            "Title": md.get("Title") or "NA",
            "Published": md.get("Published") or "NA",
            "Content": d.page_content or ""
        })
 
    return {"pubmed_data": items}
 
if __name__ == "__main__":

    mcp.run(transport="http",port=8000)
