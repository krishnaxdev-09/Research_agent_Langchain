from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.tools.tools import web_search, scrape_url
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.7
)


# 1st agent : Search Agent
def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt="""
You are a web research search agent.

Your job is to search the web for recent, reliable and relevant
information about the user's topic.

IMPORTANT:
- Always use the web_search tool.
- Do not summarize away the URLs.
- After searching, return relevant results with:
  1. Title
  2. URL
  3. Snippet
- Preserve the exact URLs returned by the web_search tool.
- Do not invent URLs.
"""
    )


# 2nd agent : Scrape Agent
def build_scrape_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt="""
You are a web scraping research agent.

Your task is to scrape ONE most relevant source from the
search results provided to you.

Rules:
1. Read the search results carefully.
2. Select ONE most relevant and reliable URL.
3. You MUST call the scrape_url tool for that URL.
4. Do not scrape multiple URLs.
5. Do not ask the user for a URL if a URL is already present.
6. Do not invent or modify the URL.
7. Prefer authoritative and reliable sources.
8. Return the scraped content along with the source URL.

Format your final response as:

Source URL:
<URL>

Scraped Content:
<content>
"""
    )


# Writer
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are an expert research writer.

Write clear, structured and insightful reports.

Important:
- Use only the information provided in the research.
- Do not invent facts, statistics or sources.
- Preserve the source URL.
- Clearly distinguish information from the search results
  and information obtained from the scraped source.
"""),

    ("human", """Write a detailed research report on the topic below.

Topic:
{topic}

Research Gathered:
{research}

Structure the report as:

- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources

In Sources, list the URLs available in the research.

Be detailed, factual and professional.
"""),
])

writer_chain = writer_prompt | llm | StrOutputParser()


# Critic
critic_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a sharp and constructive research critic. "
        "Be honest and specific."
    ),

    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
...
"""),
])

critic_chain = critic_prompt | llm | StrOutputParser()