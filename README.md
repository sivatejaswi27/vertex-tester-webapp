# 🧪 Vertex Tester - Web Application

Multi-language AI-powered unit test generation web application that leverages Google Gemini to create comprehensive test cases for your Python and Java codebases.

Access the Vertex-Tester Webapp here: https://vertex-test-app-398754751300.asia-south1.run.app/

## Features

- **Multi-Language Support**: Full support for Python and Java with automatic language detection
- **Web-Based Interface**: Beautiful Streamlit UI accessible from any browser
- **Drag & Drop Upload**: Simple file upload with support for multiple files simultaneously
- **AI-Powered Test Generation**: Uses Google Gemini 2.5 Flash to generate comprehensive unit tests
- **Language-Specific Frameworks**: Generates pytest tests for Python and JUnit-compatible tests for Java
- **Intelligent Code Analysis**: 
  - Python: AST parsing for functions, methods, and async functions
  - Java: Complete method and constructor extraction with package context
- **Class Context Detection**: Identifies functions within classes vs standalone functions  
- **Enterprise-Scale Processing**: Token management and batch processing for large codebases (195k tokens per batch)
- **Intelligent Test Creation**: Generates comprehensive tests with normal cases, edge cases, and error handling
- **Real-time Progress**: Shows AI generation progress with live status updates
- **Smart File Naming**: Automatically creates appropriately named test files (test_YourClass.py, YourClassTest.java)
- **Flexible Download Options**: Download individual test files or all files in a ZIP bundle
- **Test Preview**: View generated test code before downloading
- **Secure API Connection**: Environment-based API key management

## How to Use

### **Step 1: Installation**

1. **Clone the repository**
```bash
git clone https://github.com/sivatejaswi27/vertex-tester-webapp.git
cd vertex-tester-webapp
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

### **Step 2: Configure Google Cloud API Key**

#### **Option A: Environment Variable (Recommended)**

**Windows (PowerShell):**
```powershell
$env:GOOGLE_CLOUD_API_KEY="your-api-key-here"
```

**Windows (CMD):**
```cmd
set GOOGLE_CLOUD_API_KEY=your-api-key-here
```

**Linux/Mac:**
```bash
export GOOGLE_CLOUD_API_KEY="your-api-key-here"
```

#### **Option B: .env File**

1. Create a `.env` file in the project root:
```env
GOOGLE_CLOUD_API_KEY=your-api-key-here
```

2. Install python-dotenv:
```bash
pip install python-dotenv
```

**⚠️ Important**: Never commit your API key to Git. The `.gitignore` file is configured to exclude `.env` files.

#### **How to Get Your API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key
5. Set it using one of the methods above

### **Step 3: Run the Application**

```bash
streamlit run app.py
```

The application will automatically open in your default browser at `http://localhost:8501`

### **Step 4: Generate Unit Tests**

1. **Upload Files**: 
   - Click "Browse files" or drag and drop Python (.py) or Java (.java) files
   - You can upload multiple files at once
   - Maximum 200MB per file

2. **Review Uploaded Files**:
   - Expand "Uploaded Files Details" to see file information
   - Check detected language and target test framework
   - View total file count and size

3. **Generate Tests**:
   - Click the "🚀 Generate Unit Tests" button
   - Watch real-time progress in the "Processing Details" section
   - Wait for AI to analyze and generate comprehensive tests

4. **Download Results**:
   - **Individual Downloads**: Click "Download" next to each test file
   - **Bulk Download**: Click "📥 Download All Test Files (ZIP)" to get all tests in one archive
   - **Preview Tests**: Expand "View test_[filename]" to see the generated code

## Current Status

**Phase 1 Complete**: Code analysis and function extraction  
**Phase 2 Complete**: Gemini AI integration for actual unit test generation  
**Phase 3 Complete**: Multi-language support (Python & Java)  
**Phase 4 Complete**: Web application with Streamlit UI  
**Status**: ✅ **Fully Functional Multi-Language AI-Powered Web Application**

## Requirements

### System Requirements
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended for large files)
- Internet connection for Google Gemini API access

### Software Requirements
- Google Cloud account with Gemini API access enabled
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Python Packages
All required packages are listed in `requirements.txt`:
```txt
streamlit==1.50.0
google-generativeai==0.3.0
google-genai==0.3.0
python-multipart==0.0.6
javalang==0.13.0
tiktoken==0.8.0
```

## Project Structure

```
vertex-tester-webapp/
│
├── app.py                 # Streamlit web application UI
├── main.py                # Core test generation logic (WebUnittester class)
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules (includes API keys, venv)
├── README.md             # This file
│
├── .env                  # API key configuration (not committed to Git)
└── venv/                 # Virtual environment (not committed to Git)
```

## Output Files

The application generates language-specific test files with proper naming conventions:

### **Python Tests:**
- **test_YourClass.py** - Complete pytest-based unit tests for your classes
- **test_yourmodule.py** - Tests for module-level functions
- Includes normal cases, edge cases, and error handling tests
- Uses pytest framework with proper imports and assertions

### **Java Tests:**
- **YourClassTest.java** - Complete JUnit 5-compatible unit tests  
- **YourModuleTest.java** - Tests for class methods and constructors
- Includes method testing, constructor validation, and exception handling
- Uses JUnit 5 annotations (@Test, assertEquals, assertThrows)

### **ZIP Bundle:**
- Contains all generated test files
- Includes a README.md with usage instructions
- Organized by language and test framework

## Example Generated Tests

### **Python Input: `your_pythonfile.py`**
```python
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
```

### **Python Output: `your_testpyfile.py`**
```python
import pytest
from your_pythonfile import Calculator, factorial

class TestCalculator:
    def test_add_normal(self):
        calc = Calculator()
        assert calc.add(10, 5) == 15
    
    def test_add_negative_numbers(self):
        calc = Calculator()
        assert calc.add(-5, -3) == -8
    
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
    assert factorial(0) == 1
    
def test_factorial_negative_raises():
    with pytest.raises(ValueError) as excinfo:
        factorial(-1)
    assert "Negative numbers not allowed" in str(excinfo.value)
```

### **Java Input: `your_javafile.java`**
```java
package com.example;

public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
    
    public double divide(int a, int b) {
        if (b == 0) {
            throw new ArithmeticException("Cannot divide by zero");
        }
        return (double) a / b;
    }
}
```

### **Java Output: `your_testjavafile.java`**
```java
package com.example;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class CalculatorTest {
    
    @Test
    public void testAddNormal() {
        Calculator calc = new Calculator();
        assertEquals(15, calc.add(10, 5));
    }
    
    @Test
    public void testAddNegativeNumbers() {
        Calculator calc = new Calculator();
        assertEquals(-8, calc.add(-5, -3));
    }
    
    @Test
    public void testDivideNormal() {
        Calculator calc = new Calculator();
        assertEquals(5.0, calc.divide(10, 2), 0.001);
    }
    
    @Test
    public void testDivideByZero() {
        Calculator calc = new Calculator();
        Exception exception = assertThrows(ArithmeticException.class, () -> {
            calc.divide(10, 0);
        });
        assertTrue(exception.getMessage().contains("Cannot divide by zero"));
    }
}
```

## Supported Languages

| Language   | Parser      | Test Framework | File Extensions |
|------------|-------------|----------------|-----------------|
| Python     | AST         | pytest         | .py             |
| Java       | javalang    | JUnit 5        | .java           |

## Architecture

### **Application Flow**
```
User Upload → Language Detection → Code Parsing → Token Batching → AI Generation → Test Files → Download
```

### **Core Components**

1. **Frontend (app.py)**:
   - Streamlit-based web interface
   - File upload handling
   - Real-time progress tracking
   - Download management
   - Error handling and user feedback

2. **Backend (main.py)**:
   - `WebUnittester` class with static methods
   - Multi-language detection and parsing
   - Google Gemini AI integration
   - Token-aware batch processing
   - Test file generation and formatting

### **Key Technologies**

- **Multi-Language Detection**: Automatic file extension-based language identification
- **Language-Specific Parsers**: 
  - Python AST for complete code analysis
  - javalang for Java method and constructor extraction
- **Token Management**: 
  - Uses tiktoken for accurate token counting
  - Intelligent batching at 195,000 tokens per batch
  - Prevents API limit issues with large codebases
- **AI Integration**: 
  - Google Gemini 2.5 Flash model
  - Language-specific system prompts
  - Temperature 0.3 for deterministic output
  - Safety settings configured for code generation
- **Scalable Processing**: 
  - Batch processing for multiple files
  - Streaming output for real-time feedback
  - Efficient memory management with temporary directories

## Troubleshooting

### **Common Issues and Solutions**

#### **1. "Module not found" Error**
```bash
# Reinstall all dependencies
pip install -r requirements.txt
```

#### **2. "API Key Not Set" Warning**
Make sure you've set the environment variable:
```bash
# Check if key is set (Linux/Mac)
echo $GOOGLE_CLOUD_API_KEY

# Check if key is set (Windows PowerShell)
echo $env:GOOGLE_CLOUD_API_KEY
```

If not set, configure it using the methods in [Step 2](#step-2-configure-google-cloud-api-key).

#### **3. PowerShell Script Execution Error (Windows)**
```
File venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled
```

**Solution**: Use Command Prompt (CMD) instead:
```cmd
streamlit run app.py
```

Or install Streamlit globally:
```powershell
pip install streamlit google-generativeai google-genai tiktoken javalang
streamlit run app.py
```

#### **4. "No functions/methods found" Error**
- Ensure your Python file has valid function definitions with proper syntax
- Check that Java file has valid class and method declarations
- Verify file encoding is UTF-8
- Try a simpler file first to test the system

#### **5. Slow Test Generation**
- Large files may take 30-60 seconds per batch
- Check your internet connection
- Verify Google Gemini API quota hasn't been exceeded
- Try processing fewer files at once

#### **6. "StreamlitDuplicateElementId" Error**
This error has been fixed in the latest version. If you still see it:
```bash
# Pull latest changes from GitHub
git pull origin main

# Or download the latest version
```

#### **7. API Quota Exceeded**
```
Error: 429 Resource has been exhausted
```

**Solution**: 
- Wait a few minutes and try again
- Check your [Google Cloud quota limits](https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas)
- Consider upgrading your API plan for higher limits

#### **8. Import Errors in Generated Tests**
If generated tests have incorrect imports:
- Ensure your source files have proper module structure
- Check that class names match file names (for Java)
- Verify package declarations are correct (for Java)
- You may need to manually adjust import paths based on your project structure

## Running Tests

### **Python Tests (pytest)**
```bash
# Install pytest
pip install pytest

# Run all generated test files
pytest test_*.py

# Run specific test file (replace with your actual test filename)
pytest your_testpyfile.py

# Run with verbose output
pytest -v your_testpyfile.py

# Run with coverage (replace 'your_pythonfile' with your actual module name)
pip install pytest-cov
pytest --cov=your_pythonfile your_testpyfile.py
```

### **Java Tests (JUnit 5)**

**Using JUnit Standalone JAR:**
```bash
# Download JUnit standalone jar
wget https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.1/junit-platform-console-standalone-1.10.1.jar

# Compile test file (replace with your actual filenames)
javac -cp junit-platform-console-standalone-1.10.1.jar your_testjavafile.java your_javafile.java

# Run tests
java -jar junit-platform-console-standalone-1.10.1.jar --class-path . --scan-class-path
```

**Using Maven:**
```xml
<!-- Add to pom.xml -->
<dependency>
    <groupId>org.junit.jupiter</groupId>
    <artifactId>junit-jupiter</artifactId>
    <version>5.10.1</version>
    <scope>test</scope>
</dependency>
```

```bash
# Run all tests
mvn test

# Run specific test class (replace with your actual test class name)
mvn test -Dtest=YourTestClassName
```

## Security Best Practices

### **API Key Management**
✅ **DO:**
- Store API keys in environment variables
- Use `.env` files (excluded from Git)
- Rotate keys regularly
- Use different keys for development and production

❌ **DON'T:**
- Hardcode API keys in source code
- Commit API keys to version control
- Share API keys publicly
- Use production keys in public repositories

### **File Upload Security**
- Maximum file size: 200MB per file
- Allowed extensions: `.py`, `.java`
- Files are processed in temporary directories
- Temporary files are automatically cleaned up after processing

## Performance Optimization

### **For Large Codebases**
- Process files in smaller batches (5-10 files at a time)
- Use the ZIP download feature to reduce multiple downloads
- Close browser tabs when not in use to free memory

### **Token Usage**
- Current batch size: 195,000 tokens
- Estimated tokens per function: 100-500
- Average file processing: 1-5 batches
- Monitor your API usage in Google Cloud Console

## Deployment

### **Local Deployment**
```bash
streamlit run app.py
```

### **Google Cloud Run Deployment**
- Automatic scaling
- Secure API key management with Secret Manager
- Custom domain support
- CI/CD integration

## Team

**Vertex Tester Development Team**

**Authors:**  
• Dhulipala Siva Tejaswi  
• Kaushal Girish  
• Monish Anand  

**Hackathon Project**: Automating Unit Testing for Existing Codebase  
**Version**: 1.0.0 - Web Application  
**Date**: October 2025

## Support and Contact

### **Getting Help**
- 📖 Check this README for common issues
- 🐛 [Report bugs on GitHub Issues](https://github.com/sivatejaswi27/vertex-tester-webapp/issues)
- 💡 [Request features on GitHub](https://github.com/sivatejaswi27/vertex-tester-webapp/issues/new)

### **Links**
- **GitHub Repository**: [https://github.com/sivatejaswi27/vertex-tester-webapp](https://github.com/sivatejaswi27/vertex-tester-webapp)
- **Live Demo**: Coming Soon on Google Cloud Run
- **Documentation**: [Project Wiki](https://github.com/sivatejaswi27/vertex-tester-webapp/wiki)

---

<div align="center">

**⭐ Star this repository if you find it useful!**

**Made with ❤️ for the Automating Unit Testing Hackathon**

</div>
```

