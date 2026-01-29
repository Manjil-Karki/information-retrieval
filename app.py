import streamlit as st
import requests
import re


API_URL = "http://localhost:8000/search"
DEFAULT_TOP_K = 100

st.set_page_config(page_title="Academic Search", layout="wide")


st.markdown("""
<style>
    .block-container {
        padding-top: 4rem;
        max-width: 900px;
    }
    input[type="text"] {
        font-size: 20px;
        padding: 12px;
    }
    .result-title {
        font-size: 18px;
        font-weight: 500;
        margin-bottom: 2px;
    }
    .meta {
        color: #555;
        font-size: 14px;
    }
    mark {
        background-color: #fff3b0;
        padding: 0 3px;
    }
    .author-link {
        color: #1a0dab;
        text-decoration: none;
    }
    .author-link:hover {
        text-decoration: underline;
    }
    /* Remove form border */
    .stForm {
        border: none !important;
        padding: 0 !important;
    }
    /* Align search button vertically */
    .stButton button {
        margin-top: 0px;
        height: 51px;
    }
    /* Remove input field border for cleaner look */
    div[data-testid="stTextInput"] {
        margin-bottom: 0px;
    }
    /* Align selectbox with search bar */
    div[data-testid="stSelectbox"] {
        margin-top: 0px;
    }
    div[data-testid="stSelectbox"] > div {
        margin-top: 0px;
    }
    /* Style back arrow button */
    .back-arrow-btn button {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        font-size: 32px !important;
        padding: 0 !important;
        margin-left: -40px !important;
        color: #1a0dab !important;
        height: 51px !important;
    }
    .back-arrow-btn button:hover {
        background-color: transparent !important;
        color: #0066cc !important;
    }
</style>
""", unsafe_allow_html=True)


if "page" not in st.session_state:
    st.session_state.page = "home"
if "query" not in st.session_state:
    st.session_state.query = ""
if "results" not in st.session_state:
    st.session_state.results = []
if "sort" not in st.session_state:
    st.session_state.sort = "Relevance"


def fetch_results(query):
    try:
        response = requests.get(
            API_URL,
            params={"query": query, "k": DEFAULT_TOP_K},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Search failed: {e}")
        return []


def highlight(text, query):
    if not text or not query:
        return text
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", text)


def sort_results(results, mode):
    if mode == "Citations":
        return sorted(results, key=lambda x: x.get("citations", 0), reverse=True)
    if mode == "Year":
        return sorted(results, key=lambda x: x.get("year", 0), reverse=True)
    return results  # Relevance


def create_author_search_link(author_name):
    """Create a clickable link that searches for the author"""
    # URL encode the author name for the search query
    encoded_name = requests.utils.quote(author_name)
    return f"?query={encoded_name}"


if st.session_state.page == "home":

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        "<h1 style='text-align:center;'>Academic Search</h1>",
        unsafe_allow_html=True
    )

    with st.form("home_form", clear_on_submit=False):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            query = st.text_input(
                "Search Query",
                placeholder="Search papers, authors, or topics",
                key="home_query_input",
                label_visibility="collapsed"
            )
        
        with col2:
            submitted = st.form_submit_button("Search", use_container_width=True)

    if submitted and query.strip():
        st.session_state.query = query
        st.session_state.results = fetch_results(query)
        st.session_state.page = "results"
        st.rerun()


elif st.session_state.page == "results":

    with st.form("results_form", clear_on_submit=False):
        col1, col2, col3 = st.columns([4, 1, 1])
        
        with col1:
            query = st.text_input(
                "Search Query",
                value=st.session_state.query,
                placeholder="Search again...",
                key="results_query_input",
                label_visibility="collapsed"
            )
        
        with col2:
            submitted = st.form_submit_button("Search", use_container_width=True)
        
        with col3:
            sort_mode = st.selectbox(
                "Sort by",
                ["Relevance", "Citations", "Year"],
                index=["Relevance", "Citations", "Year"].index(st.session_state.sort),
                key="sort_mode",
                label_visibility="collapsed"
            )

    if submitted and query.strip():
        st.session_state.sort = sort_mode
        st.session_state.query = query
        st.session_state.results = fetch_results(query)
        st.rerun()

    st.divider()

    results = sort_results(st.session_state.results, st.session_state.sort)

    if not results:
        st.info("No results found.")
    else:
        st.markdown(f"**About {len(results)} results**")
        st.markdown("<br>", unsafe_allow_html=True)
        
        for pub in results:
            title = highlight(pub.get("title", ""), st.session_state.query)
            
            # Create clickable title with paper link
            if pub.get("url"):
                st.markdown(
                    f"<div class='result-title'><a href='{pub['url']}' target='_blank' style='color: #1a0dab; text-decoration: none;'>{title}</a></div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div class='result-title'>{title}</div>",
                    unsafe_allow_html=True
                )

            # Create author names with links if available
            authors_list = pub.get("authors", [])
            if authors_list:
                author_links = []
                for author in authors_list:
                    author_name = author.get("name", "")
                    # Check for profile_url (primary field in your API)
                    author_url = author.get("profile_url")
                    
                    if author_name:
                        if author_url:  # This will be False for None or empty string
                            # Create clickable author link
                            author_links.append(f'<a href="{author_url}" target="_blank" class="author-link">{author_name}</a>')
                        else:
                            # Plain text if no URL
                            author_links.append(author_name)
                
                authors_html = ", ".join(author_links)
            else:
                authors_html = ""

            # Build metadata line
            meta_parts = []
            if authors_html:
                meta_parts.append(authors_html)
            if pub.get("year"):
                meta_parts.append(str(pub.get("year")))
            if pub.get("journal"):
                meta_parts.append(pub.get("journal"))
            
            meta = " • ".join(meta_parts)

            if meta:
                st.markdown(
                    f"<div class='meta'>{meta}</div>",
                    unsafe_allow_html=True
                )

            # Citations and metrics
            st.markdown(
                f"<div class='meta'>"
                f"Citations: {pub.get('citations', 0)} | "
                f"Altmetric: {pub.get('altmetric_score', 0)}"
                f"</div>",
                unsafe_allow_html=True
            )

            st.markdown("<br>", unsafe_allow_html=True)