# vscat

VSCat is a Python script that takes in a Visual Studio project folder and creates a markdown file with a summary of each file in the project.

It does this by:
- Walking all nested files and directories
- Filtering out files that are not source code files
- Creating a markdown file with a summary of each file. The summary comes from a call to OpenAI completion using the gpt-3.5-turbo model.

## Dependencies
 
- Python 3.12+
- OpenAI Api Key with access to gpt-3.5-turbo

## Setup

1. Clone this repo.

2. Create a virtual environment on the root of this project, then activate it and install the dependencies into it.

    **Linux/MacOS**
    
    ```bash
    $ python -m venv .venv
    $ source .venv/bin/activate
    $ pip install -r requirements.txt
    ```
    
    **Windows**
    
    ```powershell
    c:\> python -m venv venv
    c:\> .\venv\Scripts\Activate
    c:\> pip install -r requirements.txt
    ```

3. Copy the **env.template** file into **.env** in the root of the project and edit to include your OpenAI API key.

    ```env
    # OPEN AI API KEY
    OPENAI_API_KEY=YOUR-KEY-HERE
    # AI SUMMARY PROMPT
    AI_PROMPT="Summarize the Visual Studio code file. In this order, provide a 3 sentence summary of the file under **Summary:**, a number list of the function/method names and a short description for each under **Functions/Methods:**, a number list of the variables and a short description for each under **Variables:** and your guess as to whether or not the file is a standard .NET structure file OR if the file contains novel and unique functionality under **Guess:**. Do not return ANY CODE, only the sections requested."
    ```
    > **Note:** The `AI_PROMPT` is the prompt that will be used to generate the summary of each file. It is a template that will be used to generate the summary. You can edit this to get different output.

## Usage

To use the script, run the following command from inside the virtual environment created in the setup step.:

**Linux/MacOS**

```bash
$ python vscat.py --source-directory "/path/to/vs/project" --output-document "./tmp/output-file-name.md" --add-ai-comments
```

**Windows**

```powershell
c:\> python vscat.py --source-directory "C:\path\to\vs\project" --output-document ".\tmp\output-file-name.md" --add-ai-comments
```

## Roadmap

- [ ] Move the file extensions to include into the .env file (with defaults if not declared).
- [ ] Add a summary of the project to the markdown file, after all the files are processed, and insert at the top.
- [ ] Add logic to filter out path/file patterns based on a regex. Multiple regex patters are supported by Regex built in OR "|" operator.