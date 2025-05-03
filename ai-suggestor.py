
import os
import importlib.util
from dotenv import load_dotenv
import sys
import time
import re
import argparse 

# --- ANSI Color Codes ---
COLOR_GREEN = '\033[92m'  # Green for success/configured/installed
COLOR_RED = '\033[91m'    # Red for errors/missing library
COLOR_YELLOW = '\033[93m' # Yellow for warnings/unclear
COLOR_BLUE = '\033[94m'   # Blue for suggestions (like pip install)
COLOR_CYAN = '\033[96m'   # Cyan for informational messages (like OK status)
COLOR_RESET = '\033[0m'  # Reset color to default

# Load environment variables from .env file (if it exists)
load_dotenv()

# --- Model configuration ---
# Keys are '1', '2', '3' to match expected command-line input.
models = {
    '1': {
        'name': 'Gemini',
        'library': 'google.generativeai',
        'api_key_var': 'GOOGLE_API_KEY',
        'model_name_var': 'GOOGLE_GEMINI_MODEL'
    },
    '2': {
        'name': 'Anthropic',
        'library': 'anthropic',
        'api_key_var': 'ANTHROPIC_API_KEY',
        'model_name_var': 'ANTHROPIC_CLAUDE_MODEL'
    },
    '3': {
        'name': 'OpenAI',
        'library': 'openai',
        'api_key_var': 'OPENAI_API_KEY',
        'model_name_var': 'OPENAI_GPT_MODEL'
    }
}

# --- Global AI Client Variables ---
# These will store the initialized AI clients after configuration.
GEMINI_MODEL_CLIENT = None
ANTHROPIC_CLIENT = None
OPENAI_CLIENT = None

# --- Helper Functions for Status Checking ---

def check_library_installed(library_name):
    """
    Check if the specified Python library is installed in the current environment.
    Returns True if found, False otherwise.
    """
    try:
        # importlib.util.find_spec is the standard way to check for package existence
        return importlib.util.find_spec(library_name) is not None
    except Exception:
        # Catch potential exceptions during the check itself
        return False

def check_env_variable(var_name):
    """
    Check if the environment variable is set, has a non-empty value,
    and is not a common placeholder string.
    Returns True if the variable is considered valid and configured, False otherwise.
    """
    value = os.getenv(var_name)

    # 1. Check if the variable is set at all or is an empty string after stripping whitespace
    if value is None or value.strip() == '':
        return False # Variable is not set or is empty

    # 2. Check for common placeholder patterns (case-insensitive comparison after stripping)
    cleaned_value = value.strip().upper()
    common_placeholders = [
        "", # Already covered by strip() == '' but included for clarity
        "YOUR_API_KEY_HERE", # Generic placeholder
        "YOUR_MODEL_NAME_HERE", # Generic placeholder
        "PLACEHOLDER",
        "NONE",
        "NULL",
        "MISSING",
        "CONFIG_ME",
        "ENTER_YOUR_KEY",
        "ADD_YOUR_MODEL",
        # --- Added specific placeholders from the user's .env file (case-insensitive) ---
        "YOUR_GOOGLE_API_KEY",
        "YOUR_GOOGLE_GEMINI_MODEL",
        "YOUR_ANTHROPIC_CLAUDE_API_KEY_HERE",
        "YOUR_ANTHROPIC_CLAUDE_MODEL_NAME_HERE",
        "YOUR_OPENAI_GPT_API_KEY_HERE",
        "YOUR_OPENAI_GPT_MODEL_NAME_HERE"
        # --- End of added placeholders ---
    ]
    if cleaned_value in common_placeholders:
        return False # Value matches a known placeholder

    return True # Variable is set, non-empty, and not a recognized placeholder


# --- Analysis Prompt ---
# (Keep the prompt as it is, it defines the AI's task)
ANALYSIS_PROMPT_TEMPLATE = """
**Role:** You are an AI designed to perform static analysis of URL strings for potential sensitive information.
**Objective:** Determine if a provided URL string, analyzed purely as text, contains patterns indicative of sensitive data.
**Constraints:**
1.  You **MUST NOT** attempt to visit, access, or validate the URL in any way. Your analysis is strictly limited to the characters and structure of the string itself.
2.  Your output **MUST BE** exactly one word: either "SENSITIVE" or "OK". No other text, explanations, or punctuation are allowed.
Analyze the following URL string ONLY based on its characters, structure, and patterns. DO NOT attempt to visit, access, or validate the URL in any way.
Based strictly on the string's characteristics, determine if it suggests the potential presence of sensitive information.
Your response MUST be *only* one of the following two single words:
- "SENSITIVE" (if the string suggests potential sensitive information)
- "OK" (if the string does not suggest potential sensitive information)

Do not include any other text, explanations, or punctuation in your response.
URL: {url_string}
"""

# --- Function to display model status and VALIDATE the chosen model ---
def validate_model_choice(chosen_model_key):
    """
    Displays the status of each AI model based on library installation and
    environment variable configuration. Validates if the chosen model
    (passed as '1', '2', or '3') is available and configured.
    Returns the validated choice key if valid and configured, None otherwise.
    """
    # The header "--- AI Model Status ---" is printed in main() before calling this function.
    model_statuses = {}
    available_models = {} # Store fully configured model keys

    # Iterate through each model defined in the 'models' dictionary
    for choice_key, config in models.items():
        model_name = config['name']
        # Check if the required library is installed
        library_installed = check_library_installed(config['library'])
        # Check if the API key environment variable is set and valid
        api_key_set = check_env_variable(config['api_key_var'])
        # Check if the model name environment variable is set and valid
        model_name_set = check_env_variable(config['model_name_var'])

        # Determine if the model is fully configured (library installed AND both env vars set)
        fully_configured = library_installed and api_key_set and model_name_set

        # Store the status details for this model
        model_statuses[choice_key] = {
            'name': model_name,
            'config': config,
            'library_installed': library_installed,
            'api_key_set': api_key_set,
            'model_name_set': model_name_set,
            'fully_configured': fully_configured
        }

        # Start building the status message for this model
        status_message = f"{choice_key}: {model_name} Models" #
        # --- Coloring Logic based on Configuration State (Adjusted to User's Latest Request) ---
        if fully_configured:
            # State 3: Library Installed AND .env Configured -> Entirely Green status
            status_message += f" ({COLOR_GREEN}Library Installed, Configured{COLOR_RESET})"
            available_models[choice_key] = model_name # Add to available models list

        elif library_installed:
            # State 2: Library Installed BUT NOT fully configured (implies config is missing)
            # User wants this state to be primarily GREEN.
            missing_configs = []
            if not api_key_set:
                missing_configs.append(config['api_key_var'])
            if not model_name_set:
                missing_configs.append(config['model_name_var'])

            # If library is installed and config is missing, show GREEN status for "Library Installed"
            # and indicate missing configuration, possibly in red.
            if missing_configs:
                 status_message += f" ({COLOR_GREEN}Library Installed{COLOR_RESET}, {COLOR_RED}Configuration Missing ({', '.join(missing_configs)}){COLOR_RESET})"
            else:
                 # Fallback state: Library installed, but neither API key nor model name is marked as missing.
                 status_message += f" ({COLOR_YELLOW}Library Installed, Configuration Status Unclear?{COLOR_RESET})"

        else: # Library is NOT installed
            # State 1: Library Not Installed -> Red status and Blue pip install suggestion
            status_message += f" ({COLOR_RED}Library Not Installed{COLOR_RESET} - Use {COLOR_BLUE}pip install {config['library']}{COLOR_RESET})"
        # --- End of Coloring Logic ---

        # Print the complete status message for the current model
        print(status_message)

    # --- Validation Part ---
    # This section validates the *specific* model chosen by the user via command line.
    print(f"\n--- Validating Chosen Model ({chosen_model_key}) ---")
    if chosen_model_key not in models:
        print(f"{COLOR_RED}Error: Invalid model choice '{chosen_model_key}' received. Must be one of {list(models.keys())}.{COLOR_RESET}")
        return None

    # Get the status of the specifically chosen model
    status = model_statuses[chosen_model_key]

    # Check if the chosen model is fully configured and available for use
    if status['fully_configured']:
        print(f"Chosen model: {status['name']} ({choice_key}) - {COLOR_GREEN}Configuration Validated.{COLOR_RESET}")
        return chosen_model_key # Return the validated key if successful
    else:
        # If the chosen model is NOT fully configured, print an error and explain why.
        print(f"{COLOR_RED}Error: Chosen model {status['name']} ({choice_key}) is not fully configured.{COLOR_RESET}")
        if not status['library_installed']:
            print(f"  Reason: Library '{status['config']['library']}' not installed.")
        else:
            # Explain which specific environment variables are missing
            missing_configs_msg = []
            if not status['api_key_set']:
                missing_configs_msg.append(status['config']['api_key_var'])
            if not status['model_name_set']:
                missing_configs_msg.append(status['config']['model_name_var'])
            print(f"  Reason: Missing environment variable(s): {', '.join(missing_configs_msg)}")
        return None # Indicate validation failure


# --- Function to configure the selected AI client ---
def configure_ai_client(model_choice_key):
    """
    Configures the selected AI client based on the validated choice key ('1', '2', or '3').
    This function is called *after* validate_model_choice has confirmed the model is ready.
    Returns True if configuration is successful, False otherwise.
    """
    global GEMINI_MODEL_CLIENT, ANTHROPIC_CLIENT, OPENAI_CLIENT

    # Safety check: Ensure the key is valid (though validate_model_choice should handle this)
    if model_choice_key not in models:
        print(f"{COLOR_RED}Internal Error: Invalid model choice key '{model_choice_key}' passed to configure_ai_client.{COLOR_RESET}")
        return False

    model_config = models[model_choice_key]
    model_name_str = model_config['name']

    # Retrieve the actual values. We expect these to be valid because
    # validate_model_choice passed and returned the key.
    api_key = os.getenv(model_config['api_key_var'])
    model_name_env = os.getenv(model_config['model_name_var'])

    # Double-check env vars just before configuring, as a final safeguard.
    if not check_env_variable(model_config['api_key_var']) or not check_env_variable(model_config['model_name_var']):
         print(f"{COLOR_RED}Internal Error: API key or model name appears invalid for {model_name_str} during configuration despite prior validation. Check .env and execution environment.{COLOR_RESET}")
         return False


    # Attempt to configure the specific client based on the chosen model key
    try:
        print(f"Configuring {model_name_str} client...")
        if model_choice_key == '1': # Gemini
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            # Attempt to create the model instance to verify the model name is likely valid
            try:
                temp_model_check = genai.GenerativeModel(model_name_env)
            except Exception as model_e:
                print(f"{COLOR_YELLOW}Warning: Configured {model_name_str} client, but the specified model name '{model_name_env}' might be invalid: {model_e}{COLOR_RESET}")
                # Decide if this warning should prevent configuration success. For now, it's a warning.
                pass

            GEMINI_MODEL_CLIENT = genai.GenerativeModel(model_name_env)
            print(f"{COLOR_GREEN}{model_name_str} client configured using model: {model_name_env}.{COLOR_RESET}")
            return True

        elif model_choice_key == '2': # Anthropic
            import anthropic
            ANTHROPIC_CLIENT = anthropic.Anthropic(api_key=api_key)
            # Add model name validation if possible with Anthropic library
            print(f"{COLOR_GREEN}{model_name_str} client configured. Will use model: {model_name_env} for calls.{COLOR_RESET}")
            return True

        elif model_choice_key == '3': # OpenAI
            import openai
            OPENAI_CLIENT = openai.OpenAI(api_key=api_key)
            # Add model name validation if possible with OpenAI library
            print(f"{COLOR_GREEN}{model_name_str} client configured. Will use model: {model_name_env} for calls.{COLOR_RESET}")
            return True

    except Exception as e:
        # Catch any errors during the API client initialization itself (e.g., invalid API key format)
        print(f"{COLOR_RED}Error configuring {model_name_str} API: {e}{COLOR_RESET}")
        # Provide specific hints for common errors
        if "api_key" in str(e).lower() or "authentication" in str(e).lower() or "401" in str(e):
            print(f"{COLOR_YELLOW}  Check if the API key for {model_name_str} is correct in your .env file.{COLOR_RESET}")
        return False # Configuration failed

    return False # Should theoretically not be reached


# --- Function to parse retry delay from error message ---
def parse_retry_delay(error_message):
    """
    Parses the retry delay in seconds from the error message string.
    Looks for patterns like 'retry_delay { seconds: XX }' or 'Retry after X seconds'.
    Returns the delay in seconds as an integer, or None if not found.
    """
    error_str = str(error_message).lower() # Case-insensitive matching for robustness

    # Pattern 1: retry_delay { seconds: XX } (Google API format)
    match1 = re.search(r'retry_delay\s*{\s*seconds:\s*(\d+)\s*}', error_str)
    if match1:
        try:
            return int(match1.group(1))
        except ValueError:
            pass # Ignore conversion error and try next pattern

    # Pattern 2: Retry after X seconds (common in various APIs)
    match2 = re.search(r'retry after (\d+)\s*seconds', error_str)
    if match2:
        try:
            return int(match2.group(1))
        except ValueError:
            pass # Ignore conversion error

    # Pattern 3: specific 429 error messages that might contain delay info (e.g., OpenAI)
    if "rate limit reached" in error_str or "quota exceeded" in error_str:
        # Attempt to extract wait time if specified, e.g., "Please try again in 20s."
        match_wait = re.search(r'try again in (\d+)s', error_str)
        if match_wait:
            try:
                return int(match_wait.group(1))
            except ValueError:
                pass
        # If specific time not found in rate limit message, use a default reasonable delay
        print(f"{COLOR_YELLOW}  Rate limit message detected, but specific delay not parsed. Using default 60s.{COLOR_RESET}")
        return 60 # Default delay for generic rate limit errors

    return None # Return None if no known retry delay pattern is found


# --- Function to analyze a single URL using the selected AI ---
def analyze_url_with_ai(model_choice_key, url):
    """
    Analyzes a single URL string using the selected AI model (identified by key '1', '2', or '3').
    Includes rate limit handling with retry delays and error handling.
    Returns True if considered sensitive, False otherwise, and None if an error occurred or response is unclear.
    Relies on the global client variables being configured *before* this function is called.
    """
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(url_string=url)
    response_text = None
    max_retries = 5 # Maximum number of retries for transient errors (like rate limits)
    retries = 0

    # Get the model configuration details needed for the API call
    if model_choice_key not in models:
        print(f"{COLOR_RED}Internal Error: Invalid model choice key '{model_choice_key}' in analyze_url_with_ai.{COLOR_RESET}")
        return None # Should not happen if called after successful validation

    model_config = models[model_choice_key]
    model_name_env_var = model_config['model_name_var']
    model_name_str = model_config['name']

    # Get the actual model name from environment variables.
    # We expect this to be valid because configure_ai_client succeeded, but add a safety check.
    if check_env_variable(model_name_env_var):
        model_name_for_api = os.getenv(model_name_env_var)
    else:
        # This indicates a serious internal error if reached, as validation/config should have caught it.
        print(f"{COLOR_RED}Internal Error: Model name configuration ({model_name_env_var}) missing or invalid for {model_name_str} during analysis call. Cannot proceed.{COLOR_RESET}")
        return None # Cannot proceed without a valid model name

    # Loop to attempt analysis with retries
    while retries < max_retries:
        try:
            # Ensure the correct global client is initialized before attempting the API call
            if model_choice_key == '1' and GEMINI_MODEL_CLIENT:
                # print(f"  -> Analyzing with Gemini ({model_name_for_api})...") # Verbose logging
                response = GEMINI_MODEL_CLIENT.generate_content(prompt)
                # Handle potential safety blocks or empty responses from the API
                if not response.parts:
                    print(f"{COLOR_YELLOW}  Warning: Gemini response blocked or empty for URL: {url}. Treating as 'OK'.{COLOR_RESET}")
                    # Decide how to handle blocked/empty responses. Defaulting to 'OK' might be safer
                    # than marking as sensitive or failing the analysis for this URL.
                    response_text = "OK" # Default to OK if blocked/empty
                else:
                    response_text = response.text.strip().upper() # Get the response text and format it

            elif model_choice_key == '2' and ANTHROPIC_CLIENT:
                # print(f"  -> Analyzing with Anthropic ({model_name_for_api})...") # Verbose logging
                message = ANTHROPIC_CLIENT.messages.create(
                    model=model_name_for_api, # Use the actual model name from env for the API call
                    max_tokens=10, # Limit tokens as we only expect "SENSITIVE" or "OK"
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                # Extract the text content from the Anthropic response object
                if message.content and isinstance(message.content, list) and len(message.content) > 0:
                    response_text = message.content[0].text.strip().upper()
                else:
                    print(f"{COLOR_YELLOW}  Warning: Received unexpected or empty content from Anthropic for URL: {url}. Treating as 'OK'.{COLOR_RESET}")
                    response_text = "OK" # Default to OK

            elif model_choice_key == '3' and OPENAI_CLIENT:
                # print(f"  -> Analyzing with OpenAI ({model_name_for_api})...") # Verbose logging
                response = OPENAI_CLIENT.chat.completions.create(
                    model=model_name_for_api, # Use the actual model name from env for the API call
                    max_tokens=10, # Limit tokens as we only expect "SENSITIVE" or "OK"
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                # Extract the text content from the OpenAI response object
                if response.choices and response.choices[0].message:
                    response_text = response.choices[0].message.content.strip().upper()
                else:
                     print(f"{COLOR_YELLOW}  Warning: Received unexpected or empty choices from OpenAI for URL: {url}. Treating as 'OK'.{COLOR_RESET}")
                     response_text = "OK" # Default to OK

            else:
                # This indicates an internal error: the chosen client was not configured.
                print(f"{COLOR_RED}Error: Client for selected model option '{model_choice_key}' ({models[model_choice_key]['name']}) is not configured. Cannot perform analysis.{COLOR_RESET}")
                return None # Indicate an error

            # --- Response Validation ---
            # Check if the AI's response is one of the expected values ("SENSITIVE" or "OK")
            if response_text == "SENSITIVE":
                return True # Analysis indicates sensitive content
            elif response_text == "OK":
                return False # Analysis indicates OK content
            else:
                # Handle unexpected responses (e.g., the model didn't follow the prompt format)
                print(f"{COLOR_YELLOW}  Warning: Received unexpected/unclear response from AI: '{response_text}'. Treating as 'OK'.{COLOR_RESET}")
                # For automation, defaulting to OK might be safer than failing.
                return False # Defaulting to OK for automation

        except Exception as e:
            # Catch any exceptions that occur during the API call
            error_message = str(e)
            print(f"{COLOR_RED}  Error during AI analysis for URL {url}: {error_message}{COLOR_RESET}")

            # --- Rate Limit Handling ---
            # Check for common rate limit indicators (status code 429, specific messages)
            if "429" in error_message or "rate limit" in error_message.lower() or "quota" in error_message.lower():
                delay = parse_retry_delay(error_message) # Attempt to parse suggested delay
                wait_time = delay if delay is not None and delay > 0 else 60 # Use parsed delay or a default

                # Wait for the specified time before attempting a retry
                print(f"{COLOR_YELLOW}  Rate limit likely hit. Waiting for {wait_time} seconds before retry {retries + 1}/{max_retries}...{COLOR_RESET}")
                time.sleep(wait_time)
                retries += 1 # Increment retry counter
                continue # Continue the while loop to attempt the API call again

            # --- Handle other potentially recoverable API errors ---
            # Example: 5xx server errors, network/connection issues
            elif "500" in error_message or "503" in error_message or "connection error" in error_message.lower() or "service unavailable" in error_message.lower():
                 wait_time = 15 * (retries + 1) # Implement a simple exponential backoff
                 print(f"{COLOR_YELLOW}  Server-side or connection error encountered. Waiting {wait_time}s before retry {retries + 1}/{max_retries}...{COLOR_RESET}")
                 time.sleep(wait_time)
                 retries += 1
                 continue # Retry

            # --- Handle Authentication Errors (usually non-recoverable without config change) ---
            elif "authenticationerror" in error_message.lower() or "invalid api key" in error_message.lower() or "401" in error_message:
                 print(f"{COLOR_RED}  Authentication Error: Please check your API key for {models[model_choice_key]['name']} in the .env file. This is a non-recoverable error for this run.{COLOR_RESET}")
                 return None # Non-recoverable error, stop processing this URL

            else:
                # For any other unhandled exceptions, print an error and stop processing this URL.
                print(f"{COLOR_RED}  An unhandled error occurred: {e}. Stopping analysis for this URL.{COLOR_RESET}")
                # Depending on the severity, you might choose to retry or log more details.
                return None # Indicate failure for this URL

    # If retries are exhausted and we still haven't returned a result
    print(f"{COLOR_RED}  Error: Failed to get a clear response after {max_retries} retries for URL: {url}. Skipping.{COLOR_RESET}")
    return None # Indicate failure after exhausting retries


# --- Main Program ---
def main():
    """Main function to handle argument parsing, file loading, processing, and saving."""

    # --- Argument Parsing ---
    # Set up argument parser to handle command-line arguments
    parser = argparse.ArgumentParser(description="Analyze URLs for sensitive content using AI.")
    parser.add_argument("input_file", help="Path to the text file containing the list of URLs.")
    parser.add_argument("concurrency", choices=['yes', 'no'], help="Concurrency setting (currently informational, 'yes' or 'no').")
    parser.add_argument("model_choice", choices=['1', '2', '3'], help="AI Model choice key (1: Gemini, 2: Anthropic, 3: OpenAI).")
    parser.add_argument("-o", "--output", default="suggestion.txt", # Default output file name
                        help="Output file path for sensitive URLs (default: suggestion.txt)")

    # Check if enough command-line arguments were provided
    # sys.argv[0] is the script name itself, so we expect at least 4 arguments (script + 3 required args)
    if len(sys.argv) < 4:
         print(f"{COLOR_RED}Error: Missing required command-line arguments.{COLOR_RESET}")
         parser.print_help() # Print usage instructions
         sys.exit(1) # Exit the script with a non-zero status code indicating an error

    # Attempt to parse the provided arguments
    try:
        args = parser.parse_args() # Parse the arguments provided via sys.argv
    except SystemExit:
        # argparse calls sys.exit() on error or when --help is used.
        return # Allow argparse's exit to proceed

    except Exception as e:
        # Catch any other unexpected errors during argument parsing
        print(f"{COLOR_RED}Error parsing arguments: {e}{COLOR_RESET}")
        parser.print_help()
        sys.exit(1)


    # Assign parsed arguments to variables
    input_filename = args.input_file
    concurrency_setting = args.concurrency # Store concurrency setting (for future use)
    model_choice_key = args.model_choice   # The user's chosen model key ('1', '2', or '3')
    output_filename = args.output         # The specified output file path


    # Print script start information
    print(f"--- Script Started ---")
    print(f"Input file: {input_filename}")
    print(f"Concurrency: {concurrency_setting}")
    print(f"Chosen AI Model Key: {model_choice_key}")
    print(f"Output file: {output_filename}")
    print(f"----------------------")

    # --- Model Status Display and Validation ---
    # Display the status of all configured models and validate the user's choice.
    print("\n--- AI Model Status ---") # Print header before listing statuses
    validated_choice = validate_model_choice(model_choice_key) # This function prints statuses and validates the chosen key

    # If validation fails (returns None), print an error and exit.
    if validated_choice is None:
        print(f"{COLOR_RED}Exiting due to model validation failure. Please check library installations and .env configuration.{COLOR_RESET}")
        sys.exit(1) # Exit with an error code

    # --- Configure the selected AI client ---
    # If validation was successful, attempt to configure the chosen AI client.
    if not configure_ai_client(validated_choice):
        # If configuration fails, print an error and exit.
        print(f"{COLOR_RED}Failed to configure the selected AI client. Exiting.{COLOR_RESET}")
        sys.exit(1) # Exit with an error code

    # --- File Processing ---
    # Read URLs from the input file and process them.
    try:
        # Ensure the input file exists before attempting to open it.
        if not os.path.exists(input_filename):
            print(f"{COLOR_RED}Error: Input file not found at '{input_filename}'. Please check the path passed from the Go script.{COLOR_RESET}")
            sys.exit(1) # Exit if input file doesn't exist

        # Open and read the input file, skipping empty lines.
        with open(input_filename, 'r', encoding='utf-8') as infile:
            urls = [line.strip() for line in infile if line.strip()] # Read non-empty lines, strip whitespace

        # If the input file was empty, print a warning and exit normally.
        if not urls:
            print(f"{COLOR_YELLOW}Warning: The input file '{input_filename}' is empty or contains only whitespace. No URLs to process.{COLOR_RESET}")
            # Optionally, ensure the output file exists even if empty.
            try:
                with open(output_filename, 'a', encoding='utf-8') as outfile:
                    pass # Just ensure the file exists or is created
            except IOError as e:
                 print(f"{COLOR_RED}Error creating or accessing output file '{output_filename}': {e}{COLOR_RESET}")
                 sys.exit(1)

            print("Analysis complete (no URLs found).")
            return # Exit normally

        # Print information about the analysis process
        print(f"\nAnalyzing {len(urls)} URLs from '{input_filename}'...")
        # Explain where potentially sensitive URLs will be saved.
        print(f"Potentially sensitive URLs will be appended to '{output_filename}'")

        sensitive_count = 0 # Counter for URLs detected as sensitive
        processed_count = 0 # Counter for URLs attempted for analysis
        error_count = 0     # Counter for URLs where analysis failed or was unclear

        # Open the output file in append mode ('a') with explicit UTF-8 encoding.
        # This will create the file if it doesn't exist or append to it if it does.
        try:
            with open(output_filename, 'a', encoding='utf-8') as outfile:
                # Process each URL from the input list
                for i, url in enumerate(urls):
                    print(f"Processing URL {i + 1}/{len(urls)}: {url}")
                    processed_count += 1 # Increment processed count for each URL

                    # Call the AI analysis function for the current URL
                    # Pass the validated model key so the function knows which client to use.
                    is_sensitive = analyze_url_with_ai(validated_choice, url)

                    # Handle the result of the analysis
                    if is_sensitive is True:
                        # If detected as sensitive, print green message and write to output file.
                        print(f"  => {COLOR_GREEN}Detected as potentially SENSITIVE. Appending to {output_filename}{COLOR_RESET}")
                        outfile.write(url + '\n')
                        sensitive_count += 1 # Increment sensitive count
                    elif is_sensitive is False:
                        # If detected as OK, print cyan message.
                        print(f"  => {COLOR_CYAN}Detected as OK.{COLOR_RESET}")
                    else: # is_sensitive is None (analysis failed or unclear)
                        # If analysis failed or response was unclear, print red message and increment error count.
                        print(f"  => {COLOR_RED}Analysis failed or unclear response. Skipping this URL.{COLOR_RESET}")
                        error_count += 1 # Increment error count

                    # Adjust the delay as needed based on the API's rate limits.
                    time.sleep(0.5) # 500ms delay between processing URLs

        except IOError as e:
             # Catch errors specifically related to writing to the output file
             print(f"{COLOR_RED}Error writing to output file '{output_filename}': {e}{COLOR_RESET}")
             sys.exit(1) # Exit with an error code

        # --- Analysis Summary ---
        # Print a summary of the analysis results
        print("\n--- Analysis Summary ---")
        print(f"Processed: {processed_count} URLs")
        print(f"Detected as Sensitive: {sensitive_count} URLs")
        print(f"Errors/Skipped: {error_count} URLs")
        print(f"Results saved/appended to: '{output_filename}'")
        print("------------------------")


    except FileNotFoundError:
        # This specific error should ideally be caught earlier when checking os.path.exists,
        # but keeping this here as a fallback.
        print(f"{COLOR_RED}Error: Input file not found at '{input_filename}'. Please check the file path.{COLOR_RESET}")
        sys.exit(1) # Exit with an error code
    except Exception as e:
        # Catch any other unexpected errors that occur during file processing or analysis loop.
        print(f"{COLOR_RED}An unexpected error occurred during URL processing: {e}{COLOR_RESET}")
        sys.exit(1) # Exit with an error code


if __name__ == "__main__":
    main()
