from src.agents.agents import (
    build_search_agent,
    build_scrape_agent,
    writer_chain,
    critic_chain
)


def run_research_pipeline(topic: str) -> dict:

    state = {}

    # ==========================================
    # STEP 1 - SEARCH AGENT
    # ==========================================

    print("\n" + "=" * 50)
    print("STEP 1 - SEARCH AGENT")
    print("=" * 50)

    search_agent = build_search_agent()

    search_result = search_agent.invoke({
        "messages": [
            (
                "user",
                f"Find recent, reliable and detailed information about: {topic}"
            )
        ]
    })

    state["search_results"] = search_result["messages"][-1].content

    print("\nSEARCH RESULTS:\n")
    print(state["search_results"])


    # ==========================================
    # STEP 2 - READER / SCRAPE AGENT
    # ==========================================

    print("\n" + "=" * 50)
    print("STEP 2 - READER AGENT")
    print("=" * 50)

    reader_agent = build_scrape_agent()

    reader_result = reader_agent.invoke({
        "messages": [
            (
                "user",
                f"""
Find the ONE most relevant and reliable URL from the
following search results about "{topic}".

Then use the scrape_url tool to scrape that URL.

Do not scrape more than one URL.

Search Results:

{state["search_results"]}
"""
            )
        ]
    })

    state["scraped_content"] = reader_result["messages"][-1].content

    print("\nSCRAPED CONTENT:\n")
    print(state["scraped_content"])


    # ==========================================
    # STEP 3 - WRITER
    # ==========================================

    print("\n" + "=" * 50)
    print("STEP 3 - WRITER")
    print("=" * 50)

    research_combined = (
        f"SEARCH RESULTS:\n"
        f"{state['search_results']}\n\n"

        f"SCRAPED SOURCE:\n"
        f"{state['scraped_content']}"
    )

    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": research_combined
    })

    print("\nFINAL REPORT:\n")
    print(state["report"])


    # ==========================================
    # STEP 4 - CRITIC
    # ==========================================

    print("\n" + "=" * 50)
    print("STEP 4 - CRITIC")
    print("=" * 50)

    state["feedback"] = critic_chain.invoke({
        "report": state["report"]
    })

    print("\nCRITIC REPORT:\n")
    print(state["feedback"])

    return state