from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.llm import get_llm

# Keeps each request small enough for Groq's free tokens-per-minute limit
_splitter = RecursiveCharacterTextSplitter(chunk_size=6000, chunk_overlap=300)


def _extract(system_prompt: str, transcript: str, empty_message: str) -> str:
    llm = get_llm(0.2)

    chain = (
        ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{text}"),
        ])
        | llm
        | StrOutputParser()
    )

    chunks = _splitter.split_text(transcript)
    if len(chunks) <= 1:
        return chain.invoke({"text": transcript})

    # Long transcript: extract from each part, then merge into one clean list
    partials = [chain.invoke({"text": c}) for c in chunks]

    merge_chain = (
        ChatPromptTemplate.from_messages([
            ("system",
             "Merge these partial lists into one final numbered list. Remove duplicates "
             "and keep owners and deadlines. If every part says nothing was found, "
             "reply exactly: {empty}"),
            ("human", "{text}"),
        ])
        | llm
        | StrOutputParser()
    )
    return merge_chain.invoke({"text": "\n\n".join(partials), "empty": empty_message})


def extract_action_items(transcript: str) -> str:
    return _extract(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all action items. For each provide:\n"
        "- Task description\n"
        "- Owner (who is responsible)\n"
        "- Deadline (if mentioned, else write 'Not specified')\n\n"
        "Format as a numbered list, with Owner and Deadline as '-' sub-lines under each item. "
        "If none found say 'No action items found.'",
        transcript,
        "No action items found.",
    )


def extract_key_decisions(transcript: str) -> str:
    return _extract(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all key decisions made. Format as a numbered list. "
        "If none found say 'No key decisions found.'",
        transcript,
        "No key decisions found.",
    )


def extract_questions(transcript: str) -> str:
    return _extract(
        "From the meeting transcript, extract all unresolved questions "
        "or topics needing follow-up. Format as a numbered list. "
        "If none found say 'No open questions found.'",
        transcript,
        "No open questions found.",
    )