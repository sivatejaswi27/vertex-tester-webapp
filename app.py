import streamlit as st
import os
from pathlib import Path
from test_generator import HierarchicalTestGenerator
from google import genai

# Page config
st.set_page_config(
    page_title="Vertex Tester - Large File Handler",
    page_icon="🧪",
    layout="wide"
)

# Initialize session state
if 'test_results' not in st.session_state:
    st.session_state.test_results = None
if 'chunks_info' not in st.session_state:
    st.session_state.chunks_info = None

# Title and description
st.title("Vertex Tester")
st.markdown("""
Generate comprehensive unit tests for large codebases using:
- **Smart Code Chunking**: Splits code into logical components (classes/functions)
- **Hierarchical Test Generation**: Creates test plan → analyzes structure → generates targeted tests
""")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Vertex AI Configuration
    st.subheader("Vertex AI Settings")
    
    api_key = st.text_input(
        "API Key",
        value="AQ.Ab8RN6KAMuExsK5BuaC48qHaoWUCn6AB3i7sJwxi4rbT0QjA8w",
        help="Your Google Cloud API key",
        type="password"
    )
    
    
    
    # Model selection
    model_name = st.selectbox(
        "Model",
        ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-001"],
        help="Pro: Better quality, Flash: Faster & cheaper"
    )
    
    # Language selection
    language = st.selectbox(
        "Programming Language",
        ["Python", "Java"],
        help="Select the language of your code"
    )
    
    # Output directory
    output_dir = st.text_input(
        "Output Directory",
        value="tests",
        help="Directory where test files will be saved"
    )
    
    st.divider()
    
    # Connection tests
    if api_key:
        try:
            # Test connection with genai.Client
            test_client = genai.Client(
                vertexai=True,
                api_key=api_key,
                
            )
            st.success(f"✓ Connected to Vertex")
        except Exception as e:
            st.error(f"Connection error: {str(e)}")

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Upload Code File")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['py', 'java'],
        help="Upload a Python (.py) or Java (.java) file"
    )
    
    if uploaded_file:
        # Read file
        code_content = uploaded_file.read().decode('utf-8')
        
        # File info
        file_size = len(code_content)
        file_lines = len(code_content.split('\n'))
        estimated_tokens = file_size // 4
        
        st.info(f"""
        **File:** {uploaded_file.name}  
        **Size:** {file_size:,} characters  
        **Lines:** {file_lines:,}  
        **Est. Tokens:** {estimated_tokens:,}
        """)
        
        # Show code preview
        with st.expander("📄 Preview Code"):
            st.code(code_content[:2000], language=language.lower())
            if len(code_content) > 2000:
                st.caption(f"... and {len(code_content) - 2000} more characters")

with col2:
    st.header("🎯 Generation Strategy")
    
    strategy_info = st.info("""
    **Combined Strategy: Smart Chunking + Hierarchical Generation**
    
    **Stage 1**: Analyze entire codebase and create test plan  
    **Stage 2**: Chunk code into logical components (classes/functions)  
    **Stage 3**: Generate targeted tests for each chunk  
    **Stage 4**: Combine into comprehensive test suite
    
    ✓ Handles files of any size  
    ✓ Maintains context across chunks  
    ✓ Generates organized, maintainable tests
    """)

# Generation section
st.divider()
st.header("Generate Tests")


if not uploaded_file:
    st.warning("⚠️ Please upload a code file")
else:
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        generate_btn = st.button(
            "Generate Tests",
            type="primary",
            use_container_width=True
        )
    
    with col_btn2:
        if st.session_state.chunks_info:
            show_chunks = st.button(
                "View Chunks",
                use_container_width=True
            )
    
    if generate_btn:
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_container = st.expander("Generation Log", expanded=True)
        
        def update_progress(message):
            with log_container:
                st.write(f"-> {message}")
        
        try:
            # Initialize generator
            generator = HierarchicalTestGenerator(
                api_key=api_key,
                model_name=model_name
            )
            generator.set_language(language.lower())
            
            progress_bar.progress(10)
            update_progress("Initializing test generator...")
            
            # Generate tests
            results = generator.generate_tests_hierarchical(
                code=code_content,
                file_name=uploaded_file.name,
                output_dir=output_dir,
                progress_callback=update_progress
            )
            
            progress_bar.progress(100)
            
            # Store in session state
            st.session_state.test_results = results
            st.session_state.chunks_info = results['chunks_info']
            
            # Success message
            st.success(f"""
            ✅ **Tests Generated Successfully!**
            
            - **Chunks processed:** {results['num_chunks']}
            - **Output file:** `{results['output_file']}`
            - **Lines generated:** {len(results['test_code'].split(chr(10)))}
            """)
            
            # Download button
            st.download_button(
                label="📥 Download",
                data=results['test_code'],
                file_name=f"test_{Path(uploaded_file.name).stem}.{language.lower()}",
                mime="text/plain"
            )
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.exception(e)

# Results section
if st.session_state.test_results:
    st.divider()
    st.header("Results")
    
    tab1, tab2, tab3 = st.tabs(["Test Plan", "Generated Tests", "Chunks Info"])
    
    with tab1:
        st.subheader("Test Plan")
        st.markdown(st.session_state.test_results['test_plan'])
    
    with tab2:
        st.subheader("Generated Test Code")
        st.code(
            st.session_state.test_results['test_code'],
            language=language.lower()
        )
    
    with tab3:
        st.subheader("Code Chunks")
        st.text(st.session_state.test_results['chunks_info'])

# Footer
st.divider()
st.caption("Powered by Google Vertex AI | Vertex Tester v2.0")