import streamlit as st
import numpy as np
import pandas as pd
import os
from pathlib import Path
import requests
import time
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st


from typing import List
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from IPython.display import Image, display
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import operator
from typing import  Annotated
from langgraph.graph import MessagesState
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.document_loaders import WikipediaLoader
from IPython.display import Markdown
import operator
from typing import List, Annotated
from typing_extensions import TypedDict
import operator
from typing import List, Annotated
from typing_extensions import TypedDict
import time
from openai import RateLimitError
from app.gpt import translator


openai_api_key = st.secrets.get("OPENAI_API_KEY")
langsmith_api_key = st.secrets.get("LANGSMITH_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["LANGSMITH_API_KEY"] = langsmith_api_key
os.environ["TAVILY_API_KEY"] = tavily_api_key

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults


llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = "langchain-academy"



### SIDE BAR KAPAMA BASLIYOR

st.set_page_config(initial_sidebar_state="collapsed")

st.markdown(
    """
<style>
    [data-testid="collapsedControl"] {
        display: none
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("""
    <style>
    /* Menü (sidebar navigation) gizle */
    section[data-testid="stSidebarNav"] {
        display: none;
    }
    /* Sağ üstteki hamburger menü gizle */
    button[title="Toggle sidebar"] {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)


### SIDE BAR KAPAMA BİTTİ


# Bu dosyanın bulunduğu dizin (app.py'nin dizini)
current_dir = Path(__file__).parent.parent

# row-data yolunu oluştur
image_path_for_logo = current_dir.parent / "row-data" / "sesa-logo-80-new.png"

# Logonun her sayfada gösterilmesi için session_state'e kaydet
if 'logo_image_path' not in st.session_state:
    st.session_state.logo_image_path = str(image_path_for_logo)

# Ana sayfada logoyu göster (isteğe bağlı, sayfalarda da gösterebilirsin)
st.image(st.session_state.logo_image_path, width=200)

st.markdown("""
    <style>
    .stApp {
        background-color: #d3d3d3; /* 1 ton açık gri */
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
    div[data-testid="pazarlama_button"] button {
        position: fixed !important;
        top: 10px !important;
        right: 10px !important;
        background-color: #444444 !important;
        color: #FFBF00 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 12px 24px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        cursor: pointer !important;
        z-index: 9999 !important;
        transition: background-color 0.3s ease !important;
    }
    div[data-testid="pazarlama_button"] button:hover {
        background-color: #555555 !important;
        color: #FFBF00 !important;
    }
    </style>
""", unsafe_allow_html=True)

# SADECE bu button'a özel container (testid kullanılıyor)
with st.container():
    st.markdown('<div data-testid="pazarlama_button">', unsafe_allow_html=True)
    if st.button("Pazarlama Menüsüne Dön", key="pazarlama"):
        st.switch_page("pages/page2.py")
    st.markdown("</div>", unsafe_allow_html=True)

import streamlit as st

# Title
st.title("AYLIK GAZETE OLUŞTURUCUSUNA HOŞGELDİN")

# Create a form with a box layout
with st.form("Gazete içeriği"):
    st.subheader("Bu Ayki Konunu Yaz")

    konu = st.text_input("Konu")

    st.write('Ajana örnek: Add in someone from a flexiable packaging industry to add an real world experience')
    ajan1 = st.text_input("Ajan 1")

    ajan2 = st.text_input("Ajan 2")

    submitted = st.form_submit_button("Submit")

    if submitted:

        st.write('🧭 İşlem başladı, lütfen bekleyin...')
        class Analyst(BaseModel):
            affiliation: str = Field(
                description="Primary affiliation of the analyst.",
            )
            name: str = Field(
                description="Name of the analyst."
            )
            role: str = Field(
                description="Role of the analyst in the context of the topic.",
            )
            description: str = Field(
                description="Description of the analyst focus, concerns, and motives.",
            )
            @property
            def persona(self) -> str:
                return f"Name: {self.name}\nRole: {self.role}\nAffiliation: {self.affiliation}\nDescription: {self.description}\n"

        class Perspectives(BaseModel):
            analysts: List[Analyst] = Field(
                description="Comprehensive list of analysts with their roles and affiliations.",
            )

        class GenerateAnalystsState(TypedDict):
            topic: str # Research topic
            max_analysts: int # Number of analysts
            human_analyst_feedback: str # Human feedback
            analysts: List[Analyst] # Analyst asking questions


        analyst_instructions="""You are tasked with creating a set of AI analyst personas. Follow these instructions carefully:

        1. First, review the research topic:
        {topic}

        2. Examine any editorial feedback that has been optionally provided to guide creation of the analysts:

        {human_analyst_feedback}

        3. Determine the most interesting themes based upon documents and / or feedback above.

        4. Pick the top {max_analysts} themes.

        5. Assign one analyst to each theme."""

        def ask_with_retry(messages, retries=3, delay=10):
            for attempt in range(retries):
                try:
                    response = llm.invoke(messages)
                    return response
                except RateLimitError:
                    if attempt < retries - 1:
                        print(f"Rate limit aşıldı, {delay} saniye bekleniyor... ({attempt+1}/{retries})")
                        time.sleep(delay)
                    else:
                        raise

        def create_analysts(state: GenerateAnalystsState):

            """ Create analysts """

            topic=state['topic']
            max_analysts=state['max_analysts']
            human_analyst_feedback=state.get('human_analyst_feedback', '')

            # Enforce structured output
            structured_llm = llm.with_structured_output(Perspectives)

            # System message
            system_message = analyst_instructions.format(topic=topic,
                                                                    human_analyst_feedback=human_analyst_feedback,
                                                                    max_analysts=max_analysts)

            # Generate question
            analysts = structured_llm.invoke([SystemMessage(content=system_message)]+[HumanMessage(content="Generate the set of analysts.")])

            # Write the list of analysis to state
            return {"analysts": analysts.analysts}

        def human_feedback(state: GenerateAnalystsState):
            """ No-op node that should be interrupted on """
            pass

        def should_continue(state: GenerateAnalystsState):
            """ Return the next node to execute """

            # Check if human feedback
            human_analyst_feedback=state.get('human_analyst_feedback', None)
            if human_analyst_feedback:
                return "create_analysts"

            # Otherwise end
            return END

        # Add nodes and edges
        builder = StateGraph(GenerateAnalystsState)
        builder.add_node("create_analysts", create_analysts)
        builder.add_node("human_feedback", human_feedback)
        builder.add_edge(START, "create_analysts")
        builder.add_edge("create_analysts", "human_feedback")
        builder.add_conditional_edges("human_feedback", should_continue, ["create_analysts", END])

        # Compile
        memory = MemorySaver()
        graph = builder.compile(interrupt_before=['human_feedback'], checkpointer=memory)

        # View
        #display(Image(graph.get_graph(xray=1).draw_mermaid_png()))

        max_analysts = 3
        topic = konu
        thread = {"configurable": {"thread_id": "1"}}

        # Run the graph until the first interruption
        for event in graph.stream({"topic":topic,"max_analysts":max_analysts,}, thread, stream_mode="values"):
            # Review
            analysts = event.get('analysts', '')
            # if analysts:
            #     for analyst in analysts:
            #         print(f"Name: {analyst.name}")
            #         print(f"Affiliation: {analyst.affiliation}")
            #         print(f"Role: {analyst.role}")
            #         print(f"Description: {analyst.description}")
            #         print("-" * 50)

        state = graph.get_state(thread)

        graph.update_state(thread, {"human_analyst_feedback":ajan1}, as_node="human_feedback")

        for event in graph.stream(None, thread, stream_mode="values"):
            # Review
            analysts = event.get('analysts', '')

        graph.update_state(thread, {"human_analyst_feedback":ajan2}, as_node="human_feedback")

        for event in graph.stream(None, thread, stream_mode="values"):
            # Review
            analysts = event.get('analysts', '')

        # If we are satisfied, then we simply supply no feedback
        further_feedack = None
        graph.update_state(thread, {"human_analyst_feedback":
                                    further_feedack}, as_node="human_feedback")

        # Continue the graph execution to end
        for event in graph.stream(None, thread, stream_mode="updates"):
            print("--Node--")
            node_name = next(iter(event.keys()))

        final_state = graph.get_state(thread)
        analysts = final_state.values.get('analysts')



        class InterviewState(MessagesState):
            max_num_turns: int # Number turns of conversation
            context: Annotated[list, operator.add] # Source docs
            analyst: Analyst # Analyst asking questions
            interview: str # Interview transcript
            sections: list # Final key we duplicate in outer state for Send() API

        class SearchQuery(BaseModel):
            search_query: str = Field(None, description="Search query for retrieval.")

        def get_analyst(state) -> Analyst:
            analyst_data = state["analyst"]
            return Analyst(**analyst_data) if isinstance(analyst_data, dict) else analyst_data


        question_instructions = """You are an newspaper writer that publishes every month, tasked with interviewing an expert to learn about a specific topic and be up to date.

        Your goal is boil down to interesting and specific insights, new trends, and new developments and new technologies related to your topic.

        1. Interesting: Insights that people will find surprising or non-obvious.

        2. Specific: Insights that avoid generalities and include specific examples from the expert.

        Here is your topic of focus and set of goals: {goals}

        Begin by introducing yourself using a name that fits your persona, and then ask your question.

        Continue to ask questions to drill down and refine your understanding of the topic.

        When you are satisfied with your understanding, complete the interview with: "Thank you so much for your help!"

        Remember to stay in character throughout your response, reflecting the persona and goals provided to you."""

        def generate_question(state: InterviewState):
            """ Node to generate a question """

            # Get state
            analyst = get_analyst(state)
            messages = state["messages"]

            # Generate question
            system_message = question_instructions.format(goals=analyst.persona)
            question = ask_with_retry([SystemMessage(content=system_message)]+messages)

            # Write messages to state
            return {"messages": [question]}

        tavily_search = TavilySearchResults(max_results=3)

        from langchain_core.messages import get_buffer_string

        # Search query writing
        search_instructions = SystemMessage(content=f"""You will be given a conversation between an analyst and an expert.

        Your goal is to generate a well-structured query for use in retrieval and / or web-search related to the conversation.

        First, analyze the full conversation.

        Pay particular attention to the final question posed by the analyst.

        Convert this final question into a well-structured web search query""")

        def search_web(state: InterviewState):
            """ Retrieve docs from web search """
            structured_llm = llm.with_structured_output(SearchQuery)
            search_query = structured_llm.invoke([search_instructions] + state['messages'])

            search_docs = tavily_search.invoke(search_query.search_query)

            # Güvenli kontrol
            formatted_search_docs = "\n\n---\n\n".join(
                [
                    f'<Document href="{doc["url"]}"/>\n{doc["content"]}\n</Document>'
                    if isinstance(doc, dict) and "url" in doc and "content" in doc
                    else f"<Document>\n{str(doc)}\n</Document>"
                    for doc in search_docs
                ]
            )

            return {"context": [formatted_search_docs]}


        def search_wikipedia(state: InterviewState):

            """ Retrieve docs from wikipedia """

            # Search query
            structured_llm = llm.with_structured_output(SearchQuery)
            search_query = structured_llm.invoke([search_instructions]+state['messages'])

            # Search
            search_docs = WikipediaLoader(query=search_query.search_query,
                                        load_max_docs=2).load()

            # Format
            formatted_search_docs = "\n\n---\n\n".join(
                [
                    f'<Document source="{doc.metadata["source"]}" page="{doc.metadata.get("page", "")}"/>\n{doc.page_content}\n</Document>'
                    for doc in search_docs
                ]
            )

            return {"context": [formatted_search_docs]}



        answer_instructions = """You are an expert being interviewed by an newspaper writer. That publishs monthly. So you need these interviews every month. You need to provide information monthly.

        Here is analyst area of focus: {goals}.

        You goal is to answer a question posed by the interviewer.

        To answer question, use this context:

        {context}

        When answering questions, follow these guidelines:

        1. Use only the information provided in the context.

        2. Do not introduce external information or make assumptions beyond what is explicitly stated in the context.

        3. The context contain sources at the topic of each individual document.

        4. Include these sources your answer next to any relevant statements. For example, for source # 1 use [1].

        5. List your sources in order at the bottom of your answer. [1] Source 1, [2] Source 2, etc

        6. If the source is: <Document source="assistant/docs/llama3_1.pdf" page="7"/>' then just list:

        [1] assistant/docs/llama3_1.pdf, page 7

        And skip the addition of the brackets as well as the Document source preamble in your citation."""

        def generate_answer(state: InterviewState):

            """ Node to answer a question """

            # Get state
            analyst = get_analyst(state)
            messages = state["messages"]
            context = state["context"]

            # Answer question
            system_message = answer_instructions.format(goals=analyst.persona, context=context)
            answer = ask_with_retry([SystemMessage(content=system_message)]+messages)

            # Name the message as coming from the expert
            answer.name = "expert"

            # Append it to state
            return {"messages": [answer]}

        def save_interview(state: InterviewState):

            """ Save interviews """

            # Get messages
            messages = state["messages"]

            # Convert interview to a string
            interview = get_buffer_string(messages)

            # Save to interviews key
            return {"interview": interview}

        def route_messages(state: InterviewState,
                        name: str = "expert"):

            """ Route between question and answer """

            # Get messages
            messages = state["messages"]
            max_num_turns = state.get('max_num_turns',2)

            # Check the number of expert answers
            num_responses = len(
                [m for m in messages if isinstance(m, AIMessage) and m.name == name]
            )

            # End if expert has answered more than the max turns
            if num_responses >= max_num_turns:
                return 'save_interview'

            # This router is run after each question - answer pair
            # Get the last question asked to check if it signals the end of discussion
            last_question = messages[-2]

            if "Thank you so much for your help" in last_question.content:
                return 'save_interview'
            return "ask_question"
        st.write('🧭 Devam ediyor, lütfen bekleyin...')

        section_writer_instructions = """You are an expert technical writer.

        Your task is to create a short, easily digestible section of a report based on a set of source documents.

        1. Analyze the content of the source documents:
        - The name of each source document is at the start of the document, with the <Document tag.

        2. Create a report structure using markdown formatting:
        - Use ## for the section title
        - Use ### for sub-section headers

        3. Write the report following this structure:
        a. Title (## header)
        b. Summary (### header)
        c. Sources (### header)

        4. Make your title engaging based upon the focus area of the analyst:
        {focus}

        5. For the summary section:
        - Set up summary with general background / context related to the focus area of the analyst
        - Emphasize what is novel, interesting, or surprising about insights gathered from the interview
        - Create a numbered list of source documents, as you use them
        - Do not mention the names of interviewers or experts
        - Aim for approximately 400 words maximum
        - Use numbered sources in your report (e.g., [1], [2]) based on information from source documents

        6. In the Sources section:
        - Include all sources used in your report
        - Provide full links to relevant websites or specific document paths
        - Separate each source by a newline. Use two spaces at the end of each line to create a newline in Markdown.
        - It will look like:

        ### Sources
        [1] Link or Document name
        [2] Link or Document name

        7. Be sure to combine sources. For example this is not correct:

        [3] https://ai.meta.com/blog/meta-llama-3-1/
        [4] https://ai.meta.com/blog/meta-llama-3-1/

        There should be no redundant sources. It should simply be:

        [3] https://ai.meta.com/blog/meta-llama-3-1/

        8. Final review:
        - Ensure the report follows the required structure
        - Include no preamble before the title of the report
        - Check that all guidelines have been followed"""

        def write_section(state: InterviewState):

            """ Node to answer a question """

            # Get state
            interview = state["interview"]
            context = state["context"]
            analyst = get_analyst(state)

            # Write section using either the gathered source docs from interview (context) or the interview itself (interview)
            system_message = section_writer_instructions.format(focus=analyst.description)
            section = ask_with_retry([SystemMessage(content=system_message)]+[HumanMessage(content=f"Use this source to write your section: {context}")])

            # Append it to state
            return {"sections": [section.content]}

        # Add nodes and edges
        interview_builder = StateGraph(InterviewState)
        interview_builder.add_node("ask_question", generate_question)
        interview_builder.add_node("search_web", search_web)
        interview_builder.add_node("search_wikipedia", search_wikipedia)
        interview_builder.add_node("answer_question", generate_answer)
        interview_builder.add_node("save_interview", save_interview)
        interview_builder.add_node("write_section", write_section)

        # Flow
        interview_builder.add_edge(START, "ask_question")
        interview_builder.add_edge("ask_question", "search_web")
        interview_builder.add_edge("ask_question", "search_wikipedia")
        interview_builder.add_edge("search_web", "answer_question")
        interview_builder.add_edge("search_wikipedia", "answer_question")
        interview_builder.add_conditional_edges("answer_question", route_messages,['ask_question','save_interview'])
        interview_builder.add_edge("save_interview", "write_section")
        interview_builder.add_edge("write_section", END)

        # Interview
        memory = MemorySaver()
        interview_graph = interview_builder.compile(checkpointer=memory).with_config(run_name="Conduct Interviews")

        # View
        #display(Image(interview_graph.get_graph().draw_mermaid_png()))

        messages = [HumanMessage(f"So you said you were writing an article on {topic}?")]
        thread = {"configurable": {"thread_id": "1"}}
        interview = interview_graph.invoke({"analyst": analysts[0], "messages": messages, "max_num_turns": 2}, thread)
        #Markdown(interview['sections'][0])




        class ResearchGraphState(TypedDict):
            topic: str # Research topic
            max_analysts: int # Number of analysts
            human_analyst_feedback: str # Human feedback
            analysts: List[Analyst] # Analyst asking questions
            sections: Annotated[list, operator.add] # Send() API key
            introduction: str # Introduction for the final report
            content: str # Content for the final report
            conclusion: str # Conclusion for the final report
            final_report: str # Final report

        from langgraph.constants import Send

        def initiate_all_interviews(state: ResearchGraphState):
            """ This is the "map" step where we run each interview sub-graph using Send API """

            # Check if human feedback
            human_analyst_feedback=state.get('human_analyst_feedback')
            if human_analyst_feedback:
                # Return to create_analysts
                return "create_analysts"

            # Otherwise kick off interviews in parallel via Send() API
            else:
                topic = state["topic"]
                return [Send("conduct_interview", {"analyst": analyst,
                                                "messages": [HumanMessage(
                                                    content=f"So you said you are writing monthly article on {topic}?"
                                                )
                                                            ]}) for analyst in state["analysts"]]

        report_writer_instructions = """You are a newspaper writer creating a report monthly on this topic:

        {topic}

        You have a team of analysts. Each analyst has done two things:

        1. They conducted an interview with an expert on a specific sub-topic.
        2. They write up their finding into a memo.

        Your task:

        1. You will be given a collection of memos from your analysts.
        2. Think carefully about the insights from each memo.
        3. Consolidate these into a crisp overall summary that ties together the central ideas from all of the memos.
        4. Summarize the central points in each memo into a cohesive single narrative.

        To format your report:

        1. Use markdown formatting.
        2. Include no pre-amble for the report.
        3. Use no sub-heading.
        4. Start your report with a single title header: ## Insights
        5. Do not mention any analyst names in your report.
        6. Preserve any citations in the memos, which will be annotated in brackets, for example [1] or [2].
        7. Create a final, consolidated list of sources and add to a Sources section with the `## Sources` header.
        8. List your sources in order and do not repeat.

        [1] Source 1
        [2] Source 2

        Here are the memos from your analysts to build your report from:

        {context}"""

        def write_report(state: ResearchGraphState):
            # Full set of sections
            sections = state["sections"]
            topic = state["topic"]

            # Concat all sections together
            formatted_str_sections = "\n\n".join([f"{section}" for section in sections])

            # Summarize the sections into a final report
            system_message = report_writer_instructions.format(topic=topic, context=formatted_str_sections)
            report = ask_with_retry([SystemMessage(content=system_message)]+[HumanMessage(content=f"Write a monthly report based upon these memos.")])
            return {"content": report.content}

        intro_conclusion_instructions = """You are a newspaper writer finishing a report on {topic} for this month

        You will be given all of the sections of the report.

        You job is to write a crisp and compelling introduction or conclusion section.

        The user will instruct you whether to write the introduction or conclusion.

        Include no pre-amble for either section.

        Target around 100 words, crisply previewing (for introduction) or recapping (for conclusion) all of the sections of the report.

        Use markdown formatting.

        For your introduction, create a compelling title and use the # header for the title.

        For your introduction, use ## Introduction as the section header.

        For your conclusion, use ## Conclusion as the section header.

        Here are the sections to reflect on for writing: {formatted_str_sections}"""

        def write_introduction(state: ResearchGraphState):
            # Full set of sections
            sections = state["sections"]
            topic = state["topic"]

            # Concat all sections together
            formatted_str_sections = "\n\n".join([f"{section}" for section in sections])

            # Summarize the sections into a final report

            instructions = intro_conclusion_instructions.format(topic=topic, formatted_str_sections=formatted_str_sections)
            intro = ask_with_retry([instructions]+[HumanMessage(content=f"Write the report introduction")])
            return {"introduction": intro.content}

        def write_conclusion(state: ResearchGraphState):
            # Full set of sections
            sections = state["sections"]
            topic = state["topic"]

            # Concat all sections together
            formatted_str_sections = "\n\n".join([f"{section}" for section in sections])

            # Summarize the sections into a final report

            instructions = intro_conclusion_instructions.format(topic=topic, formatted_str_sections=formatted_str_sections)
            conclusion = ask_with_retry([instructions]+[HumanMessage(content=f"Write the report conclusion")])
            return {"conclusion": conclusion.content}

        def finalize_report(state: ResearchGraphState):
            """ The is the "reduce" step where we gather all the sections, combine them, and reflect on them to write the intro/conclusion """
            # Save full final report
            content = state["content"]
            if content.startswith("## Insights"):
                content = content.strip("## Insights")
            if "## Sources" in content:
                try:
                    content, sources = content.split("\n## Sources\n")
                except:
                    sources = None
            else:
                sources = None

            final_report = state["introduction"] + "\n\n---\n\n" + content + "\n\n---\n\n" + state["conclusion"]
            if sources is not None:
                final_report += "\n\n## Sources\n" + sources
            return {"final_report": final_report}

        # Add nodes and edges
        builder = StateGraph(ResearchGraphState)
        builder.add_node("create_analysts", create_analysts)
        builder.add_node("human_feedback", human_feedback)
        builder.add_node("conduct_interview", interview_builder.compile())
        builder.add_node("write_report",write_report)
        builder.add_node("write_introduction",write_introduction)
        builder.add_node("write_conclusion",write_conclusion)
        builder.add_node("finalize_report",finalize_report)

        # Logic
        builder.add_edge(START, "create_analysts")
        builder.add_edge("create_analysts", "human_feedback")
        builder.add_conditional_edges("human_feedback", initiate_all_interviews, ["create_analysts", "conduct_interview"])
        builder.add_edge("conduct_interview", "write_report")
        builder.add_edge("conduct_interview", "write_introduction")
        builder.add_edge("conduct_interview", "write_conclusion")
        builder.add_edge(["write_conclusion", "write_report", "write_introduction"], "finalize_report")
        builder.add_edge("finalize_report", END)

        # Compile
        memory = MemorySaver()
        graph = builder.compile(interrupt_before=['human_feedback'], checkpointer=memory)
        #display(Image(graph.get_graph(xray=1).draw_mermaid_png()))


        # Inputs
        max_analysts = 3
        topic = konu
        thread = {"configurable": {"thread_id": "1"}}

        # Run the graph until the first interruption
        for event in graph.stream({"topic":topic,
                                "max_analysts":max_analysts},
                                thread,
                                stream_mode="values"):

            analysts = event.get('analysts', '')
            # if analysts:
            #     for analyst in analysts:
            #         print(f"Name: {analyst.name}")
            #         print(f"Affiliation: {analyst.affiliation}")
            #         print(f"Role: {analyst.role}")
            #         print(f"Description: {analyst.description}")
            #         print("-" * 50)

        # If we are satisfied, then we simply supply no feedback
        further_feedack = None
        graph.update_state(thread, {"human_analyst_feedback":
                                    further_feedack}, as_node="human_feedback")

        for event in graph.stream(None, thread, stream_mode="updates"):
            print("--Node--")
            node_name = next(iter(event.keys()))


        final_state = graph.get_state(thread)
        report = final_state.values.get('final_report')
        st.session_state["newspaper"] = report
        st.write(report)

with st.form("translation_form"):
    lang = st.selectbox("Select target language", ['TR', 'NL', 'QA', 'SE', 'PL', 'CY', 'GB', 'TN', 'GR', 'FR', 'IL',
                                                           'US', 'RO', 'BG', 'MA', 'DE', 'IT'
                                                           ])
    submitted = st.form_submit_button("Translate")

    if submitted:
        st.write("🔄 Translating, please wait...")
        translated_text = translator(st.session_state["newspaper"], target_lang=lang)
        st.subheader("Translated Report:")
        st.session_state["translated_newspaper"] = translated_text
        st.write(st.session_state["translated_newspaper"])
