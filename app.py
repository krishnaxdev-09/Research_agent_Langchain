import streamlit as st
import re

from src.pipelines.pipeline import run_research_pipeline


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SIMPLE STYLING
# ============================================================

st.markdown(
    """
    <style>
        .main {
            padding-top: 2rem;
        }

        .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .hero {
            padding: 1.5rem 0 2rem 0;
        }

        .hero-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .hero-subtitle {
            font-size: 1.05rem;
            color: #6b7280;
        }

        .pipeline-card {
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 1rem;
            background: #ffffff;
            text-align: center;
            min-height: 110px;
        }

        .pipeline-icon {
            font-size: 1.6rem;
        }

        .pipeline-title {
            font-weight: 600;
            margin-top: 0.4rem;
        }

        .pipeline-status {
            color: #6b7280;
            font-size: 0.85rem;
        }

        .section-header {
            margin-top: 2rem;
            margin-bottom: 0.75rem;
        }

        .url-text {
            font-size: 0.85rem;
            word-break: break-all;
        }

        .score {
            font-size: 2.5rem;
            font-weight: 700;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "research_result" not in st.session_state:
    st.session_state.research_result = None

if "topic" not in st.session_state:
    st.session_state.topic = ""

if "pipeline_status" not in st.session_state:
    st.session_state.pipeline_status = "Waiting"


# ============================================================
# HELPERS
# ============================================================

def get_value(data, key, default=""):
    """Safely get a value from the backend result."""
    value = data.get(key, default)

    if value is None:
        return default

    return value


def extract_score(feedback):
    """
    Try to extract a score such as:
    Score: 8/10
    Score: 8
    """
    if not feedback:
        return None

    match = re.search(
        r"score\s*:\s*(\d+(?:\.\d+)?)\s*(?:/\s*10)?",
        str(feedback),
        re.IGNORECASE,
    )

    if match:
        return match.group(1)

    return None


def extract_section(text, section_names):
    """
    Extract a section from critic output.

    This is intentionally forgiving because the critic
    output format may change slightly.
    """

    if not text:
        return None

    text = str(text)

    pattern = (
        r"(?:"
        + "|".join(re.escape(name) for name in section_names)
        + r")"
        r"\s*:?\s*"
        r"(.*?)"
        r"(?=\n\s*(?:"
        + r"|".join(
            [
                "Strengths",
                "Areas to Improve",
                "Areas for Improvement",
                "One[- ]line Verdict",
                "Verdict",
                "Conclusion",
            ]
        )
        + r")\s*:|\Z)"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if match:
        content = match.group(1).strip()

        if content:
            return content

    return None


def render_search_results(search_results):
    """Render search results without dumping the raw dictionary."""

    if not search_results:
        st.info("No search results were returned.")
        return

    search_results = str(search_results)

    # --------------------------------------------------------
    # Try Markdown table format
    # --------------------------------------------------------

    table_pattern = re.compile(
        r"\|\s*(?:#\s*\|\s*)?Title\s*\|\s*URL\s*\|\s*Snippet\s*\|"
        r"(.*)",
        re.IGNORECASE | re.DOTALL,
    )

    table_match = table_pattern.search(search_results)

    if table_match:
        rows = table_match.group(1).splitlines()

        results = []

        for row in rows:

            if not row.strip().startswith("|"):
                continue

            if "---" in row:
                continue

            cells = [cell.strip() for cell in row.strip("|").split("|")]

            if len(cells) < 3:
                continue

            if len(cells) >= 4:
                cells = cells[-3:]

            title, url, snippet = cells[0], cells[1], cells[2]

            if not url.startswith("http"):
                continue

            results.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                }
            )

        if results:
            for index, item in enumerate(results, start=1):

                with st.expander(
                    f"{index}. {item['title']}",
                    expanded=(index == 1),
                ):
                    st.markdown(
                        f"**URL:** [{item['url']}]({item['url']})"
                    )

                    st.markdown(
                        f"**Snippet:** {item['snippet']}"
                    )

            return

    # --------------------------------------------------------
    # Fallback: render readable content
    # --------------------------------------------------------

    with st.expander("View search results", expanded=True):
        st.markdown(search_results)


def extract_selected_url(scraped_content):
    """Try to find a URL inside the scraped-agent output."""

    if not scraped_content:
        return None

    urls = re.findall(
        r"https?://[^\s)\]>]+",
        str(scraped_content),
    )

    if urls:
        return urls[0].rstrip(".,\"'")

    return None


def render_scraped_content(scraped_content):
    """Render scraped source cleanly."""

    if not scraped_content:
        st.info("No scraped content was returned.")
        return

    scraped_content = str(scraped_content)

    selected_url = extract_selected_url(scraped_content)

    if selected_url:
        st.markdown("**Selected Source**")
        st.markdown(
            f"[{selected_url}]({selected_url})"
        )

    preview_length = 1200

    if len(scraped_content) > preview_length:

        st.markdown("**Preview**")

        st.markdown(
            scraped_content[:preview_length] + "..."
        )

        with st.expander("View full scraped content"):
            st.markdown(scraped_content)

    else:
        with st.expander(
            "View scraped content",
            expanded=True,
        ):
            st.markdown(scraped_content)


def render_critic(feedback):
    """Render critic feedback with graceful fallback."""

    if not feedback:
        st.info("No critic feedback was returned.")
        return

    feedback = str(feedback)

    score = extract_score(feedback)

    strengths = extract_section(
        feedback,
        ["Strengths"],
    )

    improvements = extract_section(
        feedback,
        [
            "Areas to Improve",
            "Areas for Improvement",
        ],
    )

    verdict = extract_section(
        feedback,
        [
            "One-line Verdict",
            "One line verdict",
            "Verdict",
        ],
    )

    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    if score:

        col1, col2 = st.columns([1, 3])

        with col1:
            st.metric(
                label="Research Score",
                value=f"{score}/10",
            )

    # --------------------------------------------------------
    # Parsed sections
    # --------------------------------------------------------

    parsed_anything = any(
        [
            score,
            strengths,
            improvements,
            verdict,
        ]
    )

    if strengths:
        st.markdown("### Strengths")
        st.markdown(strengths)

    if improvements:
        st.markdown("### Areas to Improve")
        st.markdown(improvements)

    if verdict:
        st.markdown("### Verdict")
        st.info(verdict)

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    if not parsed_anything:

        st.markdown(feedback)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🔬 Research Agent")

    st.markdown("---")

    st.markdown("### Pipeline")

    st.markdown("🔎 **Search**")
    st.markdown("📄 **Scrape**")
    st.markdown("✍️ **Write**")
    st.markdown("🧠 **Critic**")

    st.markdown("---")

    if st.session_state.topic:
        st.markdown("### Current Topic")
        st.caption(st.session_state.topic)

    st.markdown("### Pipeline Status")
    st.caption(st.session_state.pipeline_status)

    if st.session_state.research_result:

        search_results = get_value(
            st.session_state.research_result,
            "search_results",
        )

        if search_results:
            # Rough count for display only.
            result_count = len(
                re.findall(
                    r"https?://",
                    str(search_results),
                )
            )

            st.markdown("### Search Results")
            st.caption(f"{result_count} result(s)")


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">AI Research Agent</div>
        <div class="hero-subtitle">
            Search → Scrape → Write → Critique
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# RESEARCH INPUT
# ============================================================

st.markdown("### 🔍 Start a Research Task")

topic = st.text_input(
    "Enter your research topic",
    placeholder="e.g. Impact of AI on the global job market in 2026",
    value=st.session_state.topic,
)

start_research = st.button(
    "🚀 Start Research",
    type="primary",
    use_container_width=True,
)


# ============================================================
# START PIPELINE
# ============================================================

if start_research:

    if not topic.strip():

        st.warning(
            "Please enter a research topic before starting."
        )
        st.stop()

    st.session_state.topic = topic.strip()
    st.session_state.research_result = None
    st.session_state.pipeline_status = "Running"

    # --------------------------------------------------------
    # Pipeline overview
    # --------------------------------------------------------

    st.markdown("### Pipeline")

    stage_cols = st.columns(4)

    stages = [
        ("🔎", "Search Agent"),
        ("📄", "Reader Agent"),
        ("✍️", "Writer"),
        ("🧠", "Critic"),
    ]

    for column, (icon, name) in zip(stage_cols, stages):

        with column:

            with st.container(border=True):

                st.markdown(
                    f"<div class='pipeline-icon'>{icon}</div>",
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f"**{name}**"
                )

                st.caption("🔄 Working")

    # --------------------------------------------------------
    # Execute existing backend
    # --------------------------------------------------------

    try:

        with st.status(
            "Running research pipeline...",
            expanded=True,
        ) as status:

            st.write("🔎 Search Agent is running...")
            st.write("📄 Reader Agent will select and scrape a source.")
            st.write("✍️ Writer will generate the research report.")
            st.write("🧠 Critic will review the final report.")

            result = run_research_pipeline(
                st.session_state.topic
            )

            status.update(
                label="Research pipeline completed",
                state="complete",
                expanded=False,
            )

        st.session_state.research_result = result
        st.session_state.pipeline_status = "Completed"

    except Exception as exc:

        st.session_state.pipeline_status = "Failed"

        st.error(
            "Research pipeline failed. Please try again."
        )

        # Useful for terminal debugging without exposing
        # the traceback in the UI.
        print(
            f"[Research Pipeline Error] {type(exc).__name__}: {exc}"
        )

        st.stop()


# ============================================================
# RESULTS
# ============================================================

result = st.session_state.research_result


if result:

    # ========================================================
    # SEARCH RESULTS
    # ========================================================

    st.markdown(
        "<div class='section-header'></div>",
        unsafe_allow_html=True,
    )

    st.markdown("## 🔎 Search Results")

    search_results = get_value(
        result,
        "search_results",
    )

    render_search_results(search_results)


    # ========================================================
    # SCRAPED SOURCE
    # ========================================================

    st.markdown("## 📄 Scraped Source")

    scraped_content = get_value(
        result,
        "scraped_content",
    )

    render_scraped_content(
        scraped_content
    )


    # ========================================================
    # RESEARCH REPORT
    # ========================================================

    st.markdown("## 📝 Research Report")

    report = get_value(
        result,
        "report",
    )

    if report:

        report = str(report)

        st.markdown(report)

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                label="⬇️ Download Markdown",
                data=report,
                file_name="research_report.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with col2:
            st.download_button(
                label="⬇️ Download TXT",
                data=report,
                file_name="research_report.txt",
                mime="text/plain",
                use_container_width=True,
            )

    else:

        st.info("No research report was returned.")


    # ========================================================
    # CRITIC
    # ========================================================

    st.markdown("## 🧠 Critic Review")

    feedback = get_value(
        result,
        "feedback",
    )

    render_critic(feedback)


    # ========================================================
    # COMPLETION
    # ========================================================

    st.success(
        "Research completed successfully."
    )
else:

    # ========================================================
    # EMPTY STATE
    # ========================================================

    st.info(
        "Enter a research topic above and click "
        "**Start Research** to begin."
    )