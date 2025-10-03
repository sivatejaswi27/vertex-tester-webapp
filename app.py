"""
Vertex Tester - Streamlit Web Application

AI-powered unit test generation web interface using Google Gemini.
Upload Python files and get comprehensive test files generated automatically.

Authors: Dhulipala Siva Tejaswi, Kaushal Girish & Monish Anand
Version: 1.0.0
Date: 2025-01-30
"""

import streamlit as st
import os
import zipfile
import io
import traceback
from main import WebUnittester

# Page configuration
st.set_page_config(
    page_title="Vertex Tester - AI Unit Test Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 3rem;
        margin-bottom: 0.5rem;
        font-weight: bold;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    /* Hide deploy button - */
    .stAppDeployButton {
        display: none;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #e7f3ff;
        color: #0c5460;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #b8daff;
        margin: 1rem 0;
    }
    .feature-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Header section
    st.markdown('<h1 class="main-header">🧪 Vertex Tester</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Unit Test Generation with Google Gemini</p>', unsafe_allow_html=True)
    
    # Sidebar configuration
    configure_sidebar()

    # Hidden API key (secure)
    api_key = "AQ.Ab8RN6KAMuExsK5BuaC48qHaoWUCn6AB3i7sJwxi4rbT0QjA8w"
    
    # Main content area
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.header("📁 Upload Python Files")
        
        # File upload section
        uploaded_files = st.file_uploader(
            "Choose Python or Java files to generate tests for",
            type=['py', 'java'],  # ← Updated to support both
            accept_multiple_files=True,
            help="Select Python (.py) or Java (.java) files. Each file will be analyzed and comprehensive test files will be generated using AI.",
            key="file_uploader"
        )
        
        if uploaded_files:
            st.markdown(f'<div class="success-message">📄 <strong>{len(uploaded_files)} file(s)</strong> uploaded successfully!</div>', unsafe_allow_html=True)
    
            # Display uploaded files with language detection
            with st.expander("📋 Uploaded Files Details", expanded=True):
                total_size = sum(file.size for file in uploaded_files)
                
                # Count by language
                python_files = [f for f in uploaded_files if f.name.endswith('.py')]
                java_files = [f for f in uploaded_files if f.name.endswith('.java')]
                
                st.write(f"**Total files:** {len(uploaded_files)}")
                if python_files:
                    st.write(f"**🐍 Python files:** {len(python_files)} → pytest framework")
                if java_files:
                    st.write(f"**☕ Java files:** {len(java_files)} → JUnit framework")
                st.write(f"**📦 Total size:** {total_size:,} bytes")
                st.write("---")
                
                for i, file in enumerate(uploaded_files):
                    # Detect language icon and framework
                    if file.name.endswith('.py'):
                        icon = "🐍"
                        framework = "pytest"
                        lang_color = "#3776ab"  # Python blue
                    elif file.name.endswith('.java'):
                        icon = "☕"
                        framework = "JUnit"
                        lang_color = "#ed8b00"  # Java orange
                    else:
                        icon = "❓"
                        framework = "unknown"
                        lang_color = "#666666"
                        
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; margin: 0.5rem 0;">
                        <span style="font-size: 1.2rem; margin-right: 0.5rem;">{icon}</span>
                        <span style="font-weight: bold; margin-right: 0.5rem;">{i+1}.</span>
                        <code style="background-color: #f0f0f0; padding: 0.2rem 0.4rem; border-radius: 0.3rem; margin-right: 0.5rem;">{file.name}</code>
                        <span style="color: #666; margin-right: 0.5rem;">({file.size:,} bytes)</span>
                        <span style="color: {lang_color}; font-weight: bold;">→ {framework}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                # Generate tests button with language count
                total_langs = []
                if python_files:
                    total_langs.append(f"{len(python_files)} Python")
                if java_files:
                    total_langs.append(f"{len(java_files)} Java")
                lang_text = " + ".join(total_langs)
                
                button_text = f"🚀 Generate Unit Tests ({lang_text})"
                if st.button(button_text, type="primary", use_container_width=True):
                    if not api_key:
                        st.error("❌ Please configure your API key")
                    else:
                        process_files(uploaded_files, api_key)
        else:
            # Show sample when no files uploaded
            st.markdown('<div class="info-box">👆 <strong>Upload Python files above to get started!</strong><br>Supported: .py files with functions and classes</div>', unsafe_allow_html=True)
    
    with col2:
        st.header("ℹ️ How It Works")
        
        # Process steps
        st.markdown("**1. 📤 Upload**")
        st.write("Select Python files from your project")

        st.markdown("**2. 🔍 Analyze**") 
        st.write("AI analyzes your code structure and functions")

        st.markdown("**3. ⚡ Generate**")
        st.write("Creates comprehensive pytest-based tests")

        st.markdown("**4. 📥 Download**")
        st.write("Get your complete test files")
        
        st.markdown("---")
        
        # Sample code section
        st.subheader("📝 Example")
        
        with st.expander("Input Python Code"):
            st.code('''
# calculator.py
class Calculator:
    def add(self, a, b):
        return a + b
    
    def divide(self, a, b):
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b

def factorial(n):
    if n < 0:
        raise ValueError("Negative numbers not allowed")
    if n <= 1:
        return 1
    return n * factorial(n - 1)
            ''', language='python')
        
        with st.expander("Generated Test Output"):
            st.code('''
# test_Calculator.py
import pytest
from calculator import Calculator, factorial

class TestCalculator:
    def test_add_normal(self):
        calc = Calculator()
        assert calc.add(10, 5) == 15
    
    def test_divide_normal(self):
        calc = Calculator()
        assert calc.divide(10, 2) == 5
    
    def test_divide_zero_raises(self):
        calc = Calculator()
        with pytest.raises(ZeroDivisionError) as excinfo:
            calc.divide(5, 0)
        assert "Cannot divide by zero" in str(excinfo.value)

def test_factorial_normal():
    assert factorial(5) == 120
    
def test_factorial_negative_raises():
    with pytest.raises(ValueError):
        factorial(-1)
            ''', language='python')

def configure_sidebar():
    """Configure the sidebar with API key input and instructions"""
    
    with st.sidebar:
        st.header("🔧 Configuration")
        
       # Hidden API key - completely secure
        api_key = "AQ.Ab8RN6KAMuExsK5BuaC48qHaoWUCn6AB3i7sJwxi4rbT0QjA8w"

        # Show status without revealing key
        st.success("✅ AI Engine Ready")
        st.caption("🤖 Powered by Google Gemini AI")
        st.info("🔒 Secure API connection established")
        
        st.markdown("---")
        
        # Instructions
        st.header("📖 Quick Setup")
        st.markdown("""
        **Requirements:**
        1. 🌐 Google Cloud account
        2. 🔑 Gemini API access enabled
        3. 🎯 Valid API key
        
        **Supported Files:**
        • Python (.py) files
        • Functions and classes
        • Sync and async functions
        """)
        
        # Test coverage info
        st.header("🧪 Generated Tests Include")
        test_features = [
            "✅ Normal operation tests",
            "✅ Edge case handling", 
            "✅ Error condition tests",
            "✅ Exception validation",
            "✅ Proper imports & mocking",
            "✅ Clean pytest structure"
        ]
        
        for feature in test_features:
            st.markdown(f"<small>{feature}</small>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # About section
        st.header("👨‍💻 Team")
        st.markdown("""
        **Authors:**  
        • Dhulipala Siva Tejaswi  
        • Kaushal Girish  
        • Monish Anand  
        
        **Hackathon Project**  
        Version 1.0.0 - 2025
        """)
        
        # GitHub link placeholder
        st.markdown("---")
        st.markdown("🔗 **[View on GitHub](https://github.com/sivatejaswi27/vertex-tester-webapp)** | 🚀 **Live Demo Coming Soon**")
    
    return api_key

def process_files(uploaded_files, api_key):
    """
    Process uploaded files with multi-language support
    """
    
    # Progress tracking
    progress_container = st.container()
    
    with progress_container:
        st.subheader("🔄 Processing Multi-Language Files...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        test_files = []
        total_files = len(uploaded_files)
        
        # Create expandable section for real-time updates
        with st.expander("📊 Processing Details", expanded=True):
            processing_area = st.empty()
        
        # Process each file
        for i, uploaded_file in enumerate(uploaded_files):
            current_progress = (i + 1) / total_files
            
            # Detect language for display
            if uploaded_file.name.endswith('.py'):
                lang_icon = "🐍"
                framework = "pytest"
            elif uploaded_file.name.endswith('.java'):
                lang_icon = "☕" 
                framework = "JUnit"
            else:
                lang_icon = "❓"
                framework = "unknown"
            
            status_text.text(f"🔄 Processing {lang_icon} {uploaded_file.name}... ({i+1}/{total_files})")
            processing_area.text(f"Current: {lang_icon} {uploaded_file.name}\nFramework: {framework}\nAnalyzing and generating tests...")
            
            try:
                # Process the file with language detection
                test_content, test_filename, detected_language = WebUnittester.process_uploaded_file(
                    uploaded_file, api_key
                )
                
                if test_content and test_filename:
                    test_files.append({
                        'name': test_filename,
                        'content': test_content,
                        'original': uploaded_file.name,
                        'language': detected_language,
                        'size': len(test_content),
                        'framework': framework
                    })
                    
                    st.success(f"✅ Generated {framework} tests for {lang_icon} **{uploaded_file.name}** → `{test_filename}`")
                    processing_area.text(f"✅ Completed: {lang_icon} {uploaded_file.name}\nGenerated: {test_filename} ({framework})")
                else:
                    st.error(f"❌ Failed to generate tests for {lang_icon} **{uploaded_file.name}**")
                    processing_area.text(f"❌ Failed: {lang_icon} {uploaded_file.name}")
                
            except Exception as e:
                error_msg = str(e)
                st.error(f"❌ Error processing {lang_icon} **{uploaded_file.name}**: {error_msg}")
                
                # Show detailed error in expander for debugging
                with st.expander(f"🔍 Error Details for {uploaded_file.name}"):
                    st.code(traceback.format_exc(), language='text')
                
                processing_area.text(f"❌ Error in: {lang_icon} {uploaded_file.name}")
            
            # Update progress
            progress_bar.progress(current_progress)
        
        # Clear progress indicators
        status_text.empty()
        progress_bar.empty()
        processing_area.empty()
    
    # Display results if any tests were generated
    if test_files:
        display_results(test_files)
    else:
        st.error("❌ No test files were generated. Please check your files and API key.")

def display_results(test_files):
    """
    Display generated test files with multi-language support
    """
    
    st.markdown("---")
    st.header("🎉 Generated Test Files")
    
    # Language statistics
    python_tests = [f for f in test_files if f['language'] == 'python']
    java_tests = [f for f in test_files if f['language'] == 'java']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🐍 Python Tests", len(python_tests))
    with col2:
        st.metric("☕ Java Tests", len(java_tests))
    with col3:
        st.metric("📄 Total Files", len(test_files))
    
    st.success(f"Successfully generated **{len(test_files)}** test file(s) across multiple languages!")
    
    # Create download bundle
    zip_buffer = create_zip_bundle(test_files)
    
    # Download all files button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="📥 Download All Test Files (ZIP)",
            data=zip_buffer,
            file_name="vertex_tester_multilang_tests.zip",
            mime="application/zip",
            help="Download all generated test files in a single ZIP archive",
            use_container_width=True,
            key="download_all_tests_zip"  # ← ADD THIS LINE
        )
    
    st.markdown("---")
    
    # Display individual files grouped by language
    if python_tests:
        st.subheader("🐍 Python Tests (pytest)")
        for test_file in python_tests:
            display_individual_test_file(test_file, "🐍")
        
        if java_tests:
            st.markdown("---")
    
    if java_tests:
        st.subheader("☕ Java Tests (JUnit)")
        for test_file in java_tests:
            display_individual_test_file(test_file, "☕")

def display_individual_test_file(test_file, icon):
    """Display individual test file with language-specific styling"""
    
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"### {icon} {test_file['name']}")
            st.caption(f"Generated for: `{test_file['original']}` | Framework: **{test_file['framework']}** | Size: {test_file['size']:,} chars")
        
        with col2:
            st.download_button(
                label="💾 Download",
                data=test_file['content'],
                file_name=test_file['name'],
                mime="text/plain",
                key=f"download_{test_file['name']}_{test_file['language']}",
                help=f"Download {test_file['name']}",
                use_container_width=True
            )
        
        # Show code in expandable section with language-specific highlighting
        language_for_highlighting = "python" if test_file['language'] == "python" else "java"
        with st.expander(f"👁️ View {test_file['name']}", expanded=False):
            st.code(test_file['content'], language=language_for_highlighting)
        
        st.markdown("---")
        
def create_zip_bundle(test_files):
    """
    Create a ZIP file containing all test files
    
    Args:
        test_files: List of test file dictionaries
        
    Returns:
        bytes: ZIP file content
    """
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for test_file in test_files:
            zip_file.writestr(test_file['name'], test_file['content'])
        
        # Add a README file to the ZIP
        readme_content = """# Vertex Tester - Generated Unit Tests

This ZIP file contains AI-generated unit tests created by Vertex Tester.

## Files Included:
""" + "\n".join([f"- {tf['name']} (for {tf['original']})" for tf in test_files]) + """

## How to Use:
1. Extract all files to your project directory
2. Install pytest: `pip install pytest`
3. Run tests: `pytest test_*.py`

## Generated by:
Vertex Tester v1.0.0
Authors: Dhulipala Siva Tejaswi, Kaushal Girish & Monish Anand
"""
        zip_file.writestr("README.md", readme_content)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

if __name__ == "__main__":
    main()
