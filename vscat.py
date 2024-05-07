import os
import sys
import signal
import argparse
from openai import OpenAI
from dotenv import load_dotenv
import math

# Load environment variables
load_dotenv()

# Constants
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_PROMPT = os.getenv('AI_PROMPT')
# TODO: Move these constants to .env file with the below as defaults if not defined
MAX_TOKENS_PER_CALL = 150  # Adjust, according to model limits and desired output size
MODEL_CONTEXT_LIMIT = 16385  # Adjust based on your model's actual maximum limit
PROMPT_SIZE = len(OPENAI_PROMPT) + 2  # Estimate the prompt size

# OpenAI API client will inherit API_KEY from OPENAI_API_KEY environment variable
client = OpenAI()

# Hold some global values
processed_files_count = 0
total_tokens = 0
output_file_path = ""


def get_language(extension):
    """
    This function maps file extensions to the corresponding language identifier used by Markdown.
    If the file extension is not in the dictionary, it returns 'plaintext' as the default language.
    """

    languages = {
        '.cs': 'csharp', '.cpp': 'cpp', '.h': 'cpp',
        '.vb': 'vb', '.fs': 'fsharp', '.sql': 'sql',
        '.txt': 'text', '.md': 'markdown'
    }
    return languages.get(extension, 'plaintext')


def split_code_into_chunks(code, chunk_size):
    """
    Splits the input code into chunks of approximately `chunk_size` characters each.
    """
    num_chunks = math.ceil(len(code) / chunk_size)
    return [code[i * chunk_size: (i + 1) * chunk_size] for i in range(num_chunks)]


def get_commented_code(code):
    """
    This function sends the code to the OpenAI API to generate a summary or comments for the code.
    :param code:
    :return:
    """
    try:
        # Calculate the maximum number of characters we can pass in one request
        # while considering the prompt size and the response tokens
        chunk_size = (MODEL_CONTEXT_LIMIT - PROMPT_SIZE - MAX_TOKENS_PER_CALL) // 2

        # Split the code into manageable chunks
        code_chunks = split_code_into_chunks(code, chunk_size)

        all_comments = []
        total_tokens_used = 0

        # Prepare the prompt in chat message format
        system_message = {"role": "system", "content": "You are a helpful assistant that analyzes code and adds comments."}

        for i, chunk in enumerate(code_chunks):
            user_message = {"role": "user", "content": OPENAI_PROMPT + "\n\n" + chunk}
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # TODO: Move this into .env with a default here
                messages=[system_message, user_message],
                temperature=0.5,
                max_tokens=MAX_TOKENS_PER_CALL,
                top_p=1.0,
                stop=None
            )
            # Extract text from the response
            all_comments.append(response.choices[0].message.content.strip())
            total_tokens_used += response.usage.total_tokens

        # Concatenate all the comments to form the final response
        # If we had multiple code chunks, we need to have the GPT consolidate all the chunk comments into a single one
        if len(code_chunks) > 1:
            # TODO: In multi-chunk case, move the prompt to .env also.
            user_message = {"role": "user", "content": "Consolidate these multiple code summaries into a single entry"
                                                       + "\n\n".join(all_comments)}
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # TODO: Move this into .env with a default here
                messages=[system_message, user_message],
                temperature=0.5,
                max_tokens=MAX_TOKENS_PER_CALL,
                top_p=1.0,
                stop=None
            )
            # Extract text from the response
            all_comments.clear()
            all_comments.append(response.choices[0].message.content.strip())
            total_tokens_used += response.usage.total_tokens

        final_response = '\n\n'.join(all_comments)
        return final_response, total_tokens_used

    except Exception as e:
        print(f"Error processing OpenAI API request: {e}")
        return code, 0  # Return original code and zero tokens in case of API error


def concatenate_files(project_dir, output_filename, add_ai_comments):
    """
    This function concatenates the files in the project directory into a Markdown document.

    :param project_dir:
    :param output_filename:
    :param add_ai_comments:
    :return:
    """
    global processed_files_count
    global total_tokens
    global output_file_path

    output_file_path = output_filename
    project_dir = os.path.abspath(project_dir)
    with open(output_file_path, 'w', encoding='utf-8') as md_file:
        for root, _, files in os.walk(project_dir):
            for file in files:
                ext = os.path.splitext(file)[1]
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, start=project_dir)
                if ext in ['.cs', '.cpp', '.h', '.vb', '.fs', '.sql', '.txt', '.md']:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if add_ai_comments:
                        content, tokens_used = get_commented_code(content)
                        total_tokens += tokens_used
                    language = get_language(ext)
                    md_file.write(f"## {file}\n**{relative_path}**\n\n{content}\n\n")
                    # Flush after each file to ensure immediate writing to disk
                    md_file.flush()
                    processed_files_count += 1
                    if tokens_used == 0:
                        print(f"Processed {relative_path}")
                    else:
                        print(f"Processed {relative_path}, tokens: {tokens_used}")
                else:
                    print(f"Skipped {relative_path}")


def signal_handler(sig, frame):
    """
    This function handles the SIGINT signal (Ctrl+C) to gracefully exit the program.
    :param sig:
    :param frame:
    :return:
    """
    print(f"Generated file at: {output_file_path}")
    print(f"Processed {processed_files_count} files")
    print(f"Total tokens used: {total_tokens}")
    sys.exit(0)


def main():
    """
    This is the main function that parses the command-line arguments and calls the file concatenation function.
    :return:
    """
    # Set the signal handler
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description="Concatenate project files into a Markdown document.")
    parser.add_argument('--source-directory', type=str, required=True, help='Path to the source project directory')
    parser.add_argument('--output-document', type=str, required=True, help='Output Markdown filename')
    parser.add_argument('--add-ai-comments', action='store_true',
                        help='Add inline comments using OpenAI to the code snippets')
    args = parser.parse_args()

    concatenate_files(args.source_directory, args.output_document, args.add_ai_comments)


if __name__ == "__main__":
    main()
