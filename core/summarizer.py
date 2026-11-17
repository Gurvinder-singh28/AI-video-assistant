from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.llm import get_llm


def split_transcript(transcript: str) -> list:
    splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=200)
    return splitter.split_text(transcript)


def summarize(transcript: str) -> str:
    llm = get_llm(0.3)

    map_chain = (
        ChatPromptTemplate.from_messages([
            ("system", "Summarize this portion of a meeting transcript concisely."),
            ("human", "{text}"),
        ])
        | llm
        | StrOutputParser()
    )

    chunks = split_transcript(transcript)
    if len(chunks) == 1:
        partials = [chunks[0]]
    else:
        partials = [map_chain.invoke({"text": c}) for c in chunks]

    combine_chain = (
        ChatPromptTemplate.from_messages([
            ("system",
             "You are an expert meeting summarizer. Combine the following into one "
             "final professional meeting summary in bullet points. Use '-' for bullets."),
            ("human", "{text}"),
        ])
        | llm
        | StrOutputParser()
    )

    return combine_chain.invoke({"text": "\n\n".join(partials)})


def generate_title(transcript: str) -> str:
    llm = get_llm(0.3)

    chain = (
        ChatPromptTemplate.from_messages([
            ("system",
             "Based on the meeting transcript, generate a short professional meeting title "
             "(max 8 words). Only return the title, nothing else."),
            ("human", "{text}"),
        ])
        | llm
        | StrOutputParser()
    )

    return chain.invoke({"text": transcript[:2000]}).strip().strip('"')