from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from io import BytesIO
import uvicorn

from rag.ingest import ingest_pdf_file, ingest_url
from router import route_query_with_trace

app = FastAPI(title="Mini Agentic RAG API")

# Add CORS middleware to allow all requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.post("/load")
async def load(file: UploadFile = File(None), url: str = Form(None)):
    """
    Ingests PDF files or Web URLs into the vector DB.
    """
    if file:
        filename = file.filename
        try:
            content = await file.read()
            file_obj = BytesIO(content)
            num_chunks = ingest_pdf_file(file_obj, filename)
            return {
                "status": "success",
                "message": f"Successfully ingested {num_chunks} chunks from PDF file.",
                "chunks_ingested": num_chunks,
                "source": filename
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
            
    elif url:
        try:
            num_chunks = ingest_url(url)
            if num_chunks > 0:
                return {
                    "status": "success",
                    "message": f"Successfully ingested {num_chunks} chunks from URL.",
                    "chunks_ingested": num_chunks,
                    "source": url
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to extract content from the provided URL.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing URL: {str(e)}")
            
    else:
        raise HTTPException(status_code=400, detail="Either file or url must be provided.")

@app.post("/query")
async def query_endpoint(req: QueryRequest):
    """
    Accepts user query, runs agentic RAG and tool routing, and returns the response and trace info.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        response, trace = route_query_with_trace(req.query)
        return {
            "response": response,
            "trace": trace
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing query: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
