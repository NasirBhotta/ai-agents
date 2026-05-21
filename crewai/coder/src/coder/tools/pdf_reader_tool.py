from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import pypdf


class PDFReaderToolInput(BaseModel):
    """Input schema for the PDF reader tool."""

    file_path: str = Field(..., description="Absolute or relative path to the CV PDF file.")


class PDFReaderTool(BaseTool):
    name: str = "pdf_reader"
    description: str = (
        "Read the content of a PDF file and return extracted text. "
        "Use this when you need to extract information from a CV or resume PDF."
    )
    args_schema: Type[BaseModel] = PDFReaderToolInput

    def _run(self, file_path: str) -> str:
        try:
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            return f"An error occurred while reading the PDF: {str(e)}"
