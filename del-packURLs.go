package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"runtime"
	"strconv"
	"strings"
	"time"
)

// ANSI escape codes for colors
const (
	ColorYellow = "\x1b[33m"
	ColorCyan   = "\x1b[36m"
	ColorGreen  = "\x1b[32m" // Added green for script output
	ColorRed    = "\x1b[31m" // Added red for errors
	ColorReset  = "\x1b[0m"
)

// Defining command-line flags
var (
	extensions    string
	fetchAll      bool
	targetDomain  string // Flag for the target domain
	his200Mode    bool   // Flag for -his200 mode (batch or single)
	fetchPDFs     bool   // Flag for fetching only PDFs and running sort-keywords.py script
	singleURLMode bool   // Flag for single URL processing with -his200
	aiMode        bool   // New flag for AI suggestion mode
)

// Define the list of supported extensions based on the original filter regex
var supportedExtensions = []string{
	"xls", "xml", "xlsx", "json", "pdf", "sql", "doc", "docx", "pptx", "txt",
	"git", "zip", "tar.gz", "tgz", "bak", "7z", "rar", "log", "cache", "secret",
	"db", "backup", "yml", "gz", "config", "csv", "yaml", "md", "md5", "exe",
	"dll", "bin", "ini", "bat", "sh", "tar", "deb", "rpm", "iso", "img", "env",
	"apk", "msi", "dmg", "tmp", "crt", "pem", "key", "pub", "asc",
}

func init() {
	// Define the flag for specific extensions: -exts "pdf,docx,xlsx"
	flag.StringVar(&extensions, "exts", "", "Comma-separated list of file extensions to filter (e.g., \"pdf,docx,xlsx\")")
	// Define the flag to fetch all supported extensions: -all
	flag.BoolVar(&fetchAll, "all", false, "Fetch results for all supported extensions")
	// Modified flag to accept the domain instead of the full URL pattern
	flag.StringVar(&targetDomain, "domain", "", "Target domain (e.g., \"kiet.edu\")")
	// Flag for -his200 mode (batch or single)
	flag.BoolVar(&his200Mode, "his200", false, "Automatically perform 200 status check and save results to archived200.txt")
	// Flag for fetching only PDFs and running Python script
	flag.BoolVar(&fetchPDFs, "pdf", false, "Fetch only PDF files and automatically run sort-keywords.py script (saves sensitive URLs to sorted-keywords.txt)")
	// Flag for single URL processing with -his200
	flag.BoolVar(&singleURLMode, "su", false, "Enable single URL processing after fetching filtered output when using -his200")
	// New flag for fetching only PDFs and running ai-suggestor.py
	flag.BoolVar(&aiMode, "ai", false, "Fetch only PDF files and run ai-suggestor.py for sensitive PDF suggestion (saves to suggestion.txt)")

	// Default help message
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s [options] <target_domain>\n", os.Args[0])
		fmt.Fprintln(os.Stderr, "\nOptions:")
		flag.PrintDefaults()
		fmt.Fprintln(os.Stderr, "\nExamples:")
		fmt.Fprintln(os.Stderr, " 	🤓☝️  Fetch all supported extensions for a domain and stop")
		fmt.Fprintln(os.Stderr, " 	go run main.go -domain \"unschool.in\" -all")
		fmt.Fprintln(os.Stderr, " 	🤓☝️  Fetch specific extensions for a domain and stop")
		fmt.Fprintln(os.Stderr, " 	go run main.go -domain \"unschool.in\" -exts \"pdf,txt\"")
		fmt.Fprintln(os.Stderr, " 	🤓☝️  Automatically fetch and check 200 status for all extensions (Batch Mode)")
		fmt.Fprintln(os.Stderr, " 	go run main.go -domain \"unschool.in\" -all -his200")
		fmt.Fprintln(os.Stderr, " 	🤓☝️  Automatically fetch and check 200 status for specific extensions (Batch Mode)")
		fmt.Fprintln(os.Stderr, " 	go run main.go -domain \"unschool.in\" -exts pdf -his200")
		fmt.Fprintln(os.Stderr, " 	🤓☝️  Fetch, save filtered output, then check 200 status for a SINGLE selected URL (can check multiple)")
		fmt.Fprintln(os.Stderr, " 	go run main.go -domain \"unschool.in\" -all -his200 -su")
		fmt.Fprintln(os.Stderr, " 	🤓☝️  Fetch only PDFs and automatically run sort-keywords.py (saves to sorted-keywords.txt)")
		fmt.Fprintln(os.Stderr, " 	go run main.go -domain \"unschool.in\" -pdf")
		fmt.Fprintln(os.Stderr, " 	🤓☝️  Fetch only PDFs and run ai-suggestor.py for sensitive PDF suggestion (saves to suggestion.txt)")
		fmt.Fprintln(os.Stderr, " 	go run main.go -domain \"unschool.in\" -ai")
		fmt.Fprintln(os.Stderr, " 	🤓☝️  Interactive mode (will prompt for domain and options)")
		fmt.Fprintln(os.Stderr, " 	go run main.go")
		fmt.Fprintln(os.Stderr, "\nNote: The '-pdf' flag requires the 'sort-keywords.py' script and Python to be available.")
		fmt.Fprintln(os.Stderr, "Note: The '-ai' flag requires the 'ai-suggestor.py' script and Python to be available.")
		fmt.Fprintln(os.Stderr, "Note: The '-su' flag is only effective when used with '-his200'.")
	}
}

func main() {
	// Parse the command-line flags
	flag.Parse()

	// --- Start timing ---
	startTime := time.Now()

	reader := bufio.NewReader(os.Stdin)

	// Get the target domain - prioritize flag, then prompt
	if targetDomain == "" {
		// Check if there's a non-flag argument provided as the domain
		if flag.NArg() > 0 {
			targetDomain = flag.Arg(0)
		} else {
			// Modified prompt to ask only for the domain
			fmt.Print("Enter Target Domain ( e.g : kiet.edu ) : ")
			inputDomain, _ := reader.ReadString('\n')
			targetDomain = strings.TrimSpace(inputDomain)
		}
	}

	if targetDomain == "" {
		log.Fatal("Error: Target domain is required. Use -domain flag or provide as argument.")
	}

	// Construct the full target URL pattern from the domain
	targetURLPattern := fmt.Sprintf("*.%s/*", targetDomain)

	var extensionsToFilter []string
	validRequestedExtsMap := make(map[string]bool) // To count results later

	// Determine which extensions to use based on flags or prompts
	if fetchPDFs || aiMode {
		extensionsToFilter = []string{"pdf"}
		if fetchPDFs {
			fmt.Println("Fetching only PDF files for keyword scan.")
		}
		if aiMode {
			fmt.Println("Fetching only PDF files for AI suggestion.")
		}
	} else if fetchAll {
		extensionsToFilter = supportedExtensions
		fmt.Println("Fetching results for all supported extensions.")
	} else if extensions != "" {
		fmt.Printf("Using extensions from -exts flag: %s\n", extensions)
		extsSlice := strings.Split(extensions, ",")
		for _, ext := range extsSlice {
			cleanedExt := strings.TrimSpace(ext)
			if cleanedExt != "" {
				extensionsToFilter = append(extensionsToFilter, cleanedExt)
			}
		}
		if len(extensionsToFilter) == 0 {
			log.Fatal("Error: No valid extensions provided with the -exts flag.")
		}
	} else if !his200Mode && !fetchPDFs && !aiMode {
		// Only enter interactive mode if none of the modes are set
		fmt.Print("Enter extension flag ( -all / -exts / -pdf / -ai ) : ")
		extFlagInput, _ := reader.ReadString('\n')
		extFlagInput = strings.TrimSpace(extFlagInput)
		switch extFlagInput {
		case "-all":
			extensionsToFilter = supportedExtensions
			fmt.Println("Fetching results for all supported extensions.")
		case "-exts":
			fmt.Println("Supported file extensions for filtering:")
			fmt.Println(strings.Join(supportedExtensions, ", "))
			fmt.Println("-----------------------------------------")
			fmt.Print("Enter comma-separated extensions to filter (e.g., pdf,docx,txt): ")
			inputExtensions, _ := reader.ReadString('\n')
			inputExtensions = strings.TrimSpace(inputExtensions)
			requestedExtsSlice := strings.Split(inputExtensions, ",")
			for _, ext := range requestedExtsSlice {
				cleanedExt := strings.TrimSpace(ext)
				if cleanedExt != "" {
					extensionsToFilter = append(extensionsToFilter, cleanedExt)
				}
			}
			if len(extensionsToFilter) == 0 {
				log.Fatal("Error: No valid extensions entered.")
			}
		case "-pdf":
			extensionsToFilter = []string{"pdf"}
			fetchPDFs = true // Set the flag based on interactive choice
			fmt.Println("Fetching only PDF files for keyword scan.")
		case "-ai":
			extensionsToFilter = []string{"pdf"}
			aiMode = true // Set the flag based on interactive choice
			fmt.Println("Fetching only PDF files for AI suggestion.")
		default:
			log.Fatalf("Error: Invalid extension flag input. Use -all, -exts, -pdf, or -ai.")
		}
	} else if his200Mode && len(extensionsToFilter) == 0 {
		// In his200Mode but no extension flags provided, default to all supported extensions
		extensionsToFilter = supportedExtensions
		fmt.Println("In -his200 mode, no extension flag provided, defaulting to all supported extensions.")
	} else if len(extensionsToFilter) == 0 {
		// Catch-all if somehow no extensions were selected (e.g., only -his200 was used without -all or -exts)
		extensionsToFilter = supportedExtensions
		fmt.Println("No specific extensions requested, defaulting to all supported extensions.")
	}

	// Populate the map for counting using the determined extensionsToFilter
	for _, ext := range extensionsToFilter {
		validRequestedExtsMap[strings.ToLower(ext)] = true
	}

	// Construct the regex part for the filter: (ext1|ext2|...)
	filterRegexParts := []string{}
	for _, ext := range extensionsToFilter {
		escapedExt := strings.ReplaceAll(ext, ".", "\\.")
		filterRegexParts = append(filterRegexParts, escapedExt)
	}
	regexPart := "(" + strings.Join(filterRegexParts, "|") + ")"

	// Construct the full filter string value
	filterValue := fmt.Sprintf("original:.*\\.%s$", regexPart)

	// Base URL for the initial fetch
	baseURL := "https://web.archive.org/cdx/search/cdx"

	// Manually construct the full URL string using the constructed targetURLPattern
	fetchURL := baseURL + "?" +
		"url=" + url.QueryEscape(targetURLPattern) + // For decoding URL ( remove url,QueryEscape from both url line 219 and &filter line 223)
		"&collapse=urlkey" +
		"&output=text" +
		"&fl=original" +
		"&filter=" + url.QueryEscape(filterValue)

	outputPath := "filtered_output.txt" // Output file name for the initial fetch

	// Create an HTTP client with a timeout
	client := http.Client{
		Timeout: 300 * time.Second, // Increased timeout for initial fetch
	}

	// --- DEBUG PRINT: Show the constructed URL ---
	fmt.Printf("\n--- Debug: Constructed Fetch CDX API URL ---\n%s\n-------------------------------------\n", fetchURL)

	fmt.Printf("Making GET request to: %s\n", fetchURL)
	fmt.Printf("Filtering for extensions: %s\n", strings.Join(extensionsToFilter, ", "))
	fmt.Printf("Saving output to: %s\n", outputPath)

	// --- Start fetch timing ---
	startTimeFetch := time.Now()

	// Make hashing-based deduplication GET request for fetching URLs
	resp, err := client.Get(fetchURL)
	if err != nil {
		log.Fatalf("Error making HTTP request for fetch: %v", err)
	}
	defer resp.Body.Close()

	// Check if the request was successful (status code 200)
	if resp.StatusCode != http.StatusOK {
		responseBodyBytes, readErr := io.ReadAll(resp.Body)
		if readErr != nil {
			log.Printf("Error reading response body after non-200 status: %v", readErr)
		}
		log.Fatalf("Received non-200 status code (%d %s) for fetch.\nResponse Body (if available):\n%s",
			resp.StatusCode, resp.Status, string(responseBodyBytes))
	}

	// Read the entire response body into a buffer
	responseBodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Fatalf("Error reading response body for fetch: %v", err)
	}
	bodyBuffer := bytes.NewBuffer(responseBodyBytes)

	// --- DEBUG PRINT: Read and show first few bytes of response body from the buffer ---
	peekSize := 512
	fmt.Println("\n--- Debug: First few bytes of Fetch Response Body ---")
	if bodyBuffer.Len() > 0 {
		fmt.Println(bodyBuffer.String()[:min(bodyBuffer.Len(), peekSize)])
	} else {
		fmt.Println("[Fetch response body is empty]")
	}
	fmt.Println("--------------------------------------------------")

	// Create the output file
	outFile, err := os.Create(outputPath)
	if err != nil {
		log.Fatalf("Error creating output file %s: %v", outputPath, err)
	}
	defer outFile.Close() // Ensure file is closed

	// Write the content of the buffer to the file
	bytesWritten, err := io.Copy(outFile, bytes.NewReader(responseBodyBytes))
	if err != nil {
		// Close the file before fatal logging if writing failed
		outFile.Close()
		log.Fatalf("Error writing response body to file %s: %v", outputPath, err)
	}
	// Explicitly close the file after successful write
	err = outFile.Close()
	if err != nil {
		log.Printf("Warning: Error closing output file %s after write: %v", outputPath, err)
	}

	// --- End timing after saving the file ---
	fetchEndTime := time.Now()
	fetchDuration := fetchEndTime.Sub(startTimeFetch)

	fmt.Printf("Successfully saved %d bytes to %s\n", bytesWritten, outputPath)
	fmt.Printf("Fetch and save duration: %s\n", fetchDuration)

	// --- Parse the output file and count results per extension ---
	fmt.Println("\n--- Results Summary ---")

	readFileForCount, err := os.Open(outputPath)
	if err != nil {
		log.Fatalf("Error opening output file %s for reading: %v", outputPath, err)
	}
	defer readFileForCount.Close()

	scannerForCount := bufio.NewScanner(readFileForCount)
	extensionCounts := make(map[string]int)

	for ext := range validRequestedExtsMap {
		extensionCounts[ext] = 0
	}

	totalResults := 0
	for scannerForCount.Scan() {
		line := scannerForCount.Text()
		if line == "" { // Skip empty lines
			continue
		}
		totalResults++

		lowerLine := strings.ToLower(line)
		for requestedExt := range validRequestedExtsMap {
			// Check suffix more robustly, considering potential query parameters etc.
			// This is a basic check, could be refined if needed.
			if strings.HasSuffix(lowerLine, "."+requestedExt) {
				extensionCounts[requestedExt]++
				break // Count only once per line even if it matches multiple (unlikely)
			}
		}
	}

	if err := scannerForCount.Err(); err != nil {
		log.Fatalf("Error reading output file %s: %v", outputPath, err)
	}

	fmt.Println("Counts per extension:")
	for ext, count := range extensionCounts {
		fmt.Printf("Found %d results for .%s\n", count, ext)
	}
	fmt.Printf("Total results found: %d\n", totalResults)

	// --- End total time for fetch and count ---
	endTimeFetchCount := time.Now()
	totalDurationFetchCount := endTimeFetchCount.Sub(startTimeFetch) // Relative to fetch start
	fmt.Printf("Total fetch and count duration: %s\n", totalDurationFetchCount)

	// Perform secondary actions based on flags
	if his200Mode {
		urlsToCheck, readErr := readURLsFromFile(outputPath)
		if readErr != nil {
			log.Fatalf("Error reading URLs from %s for 200 check: %v", outputPath, readErr)
		}

		if len(urlsToCheck) == 0 {
			fmt.Println("No URLs found in the output file to check for 200 status.")
			createEmptyArchived200File()
		} else {
			archived200Path := "archived200.txt"
			archived200File, fileErr := os.Create(archived200Path)
			if fileErr != nil {
				log.Fatalf("Error creating output file %s for 200 links: %v", archived200Path, fileErr)
			}
			defer archived200File.Close()

			if singleURLMode {
				fmt.Println("\n--- Single URL Processing Mode for 200 Status Codes ---")
				for {
					fmt.Printf("Select a URL from %s to check for 200 status:\n", outputPath)
					for i, u := range urlsToCheck {
						fmt.Printf("%d: %s\n", i+1, u)
					}
					fmt.Print("Enter the number of the URL you want to check (or 0 to exit): ")
					inputNumberStr, _ := reader.ReadString('\n')
					inputNumberStr = strings.TrimSpace(inputNumberStr)
					chosenIndex, err := strconv.Atoi(inputNumberStr)
					if err != nil || chosenIndex < 0 || chosenIndex > len(urlsToCheck) {
						fmt.Println("Invalid selection. Please enter a valid number or 0 to exit.")
						continue
					}
					if chosenIndex == 0 {
						fmt.Println("Exiting single URL check mode.")
						break
					}
					chosenURL := urlsToCheck[chosenIndex-1]
					fmt.Printf("Checking single URL: %s%s%s\n", ColorYellow, chosenURL, ColorReset)
					startTime200Check := time.Now()
					resultsFound := getWayback200URLs(chosenURL, archived200File)
					endTime200Check := time.Now()
					duration200Check := endTime200Check.Sub(startTime200Check)
					fmt.Printf("Single URL 200 status check duration: %s\n", duration200Check)
					if resultsFound == 0 {
						fmt.Println("Failed!")
					}
					fmt.Print("Do you want to check another URL? (yes/no): ")
					checkAnotherInput, _ := reader.ReadString('\n')
					checkAnotherInput = strings.TrimSpace(strings.ToLower(checkAnotherInput))
					if checkAnotherInput != "yes" && checkAnotherInput != "y" {
						break
					}
					fmt.Println(strings.Repeat("-", 50))
				}
			} else {
				fmt.Println("\n--- Automatically Checking for 200 Status Codes (Batch Mode) ---")
				fmt.Printf("Saving 200 status links to: %s\n", archived200Path)
				startTime200Check := time.Now()
				check200Archives(urlsToCheck, archived200File)
				endTime200Check := time.Now()
				duration200Check := endTime200Check.Sub(startTime200Check)
				fmt.Printf("Total 200 status check duration (Batch Mode): %s\n", duration200Check)
			}
		}
	}

	// --- Python Script Execution Logic ---
	var concurrencyChoice string // Define locally
	var aiModelChoice string     // Define locally for AI model

	if fetchPDFs {
		fmt.Println("\n--- Running sort-keywords.py for PDF Keyword Scan ---")
		fmt.Println("Sensitive PDF URLs will be saved to sorted-keywords.txt")
		fmt.Println("Note: Using concurrency may prevent the script from stopping immediately with Ctrl+C.")
		fmt.Println("For easier stopping with Ctrl+C, choose 'no' for concurrency.")
		fmt.Print("Do you want to use concurrency in sort-keywords.py? (yes/no): ")
		concurrencyInput, _ := reader.ReadString('\n') // Use reader instead of Scanln
		concurrencyChoice = strings.TrimSpace(strings.ToLower(concurrencyInput))
		if concurrencyChoice != "yes" && concurrencyChoice != "y" {
			concurrencyChoice = "no"
		} else {
			concurrencyChoice = "yes"
		}

		startTimePython := time.Now()
		// Pass only necessary args: script, input file, concurrency
		err := runPythonScript("sort-keywords.py", outputPath, concurrencyChoice, "") // Pass empty string for model choice
		if err != nil {
			log.Printf("Error executing sort-keywords.py: %v", err)
		} else {
			fmt.Printf("sort-keywords.py finished execution.\n")
		}
		endTimePython := time.Now()
		durationPython := endTimePython.Sub(startTimePython)
		fmt.Printf("sort-keywords.py execution duration: %s\n", durationPython)
	}

	if aiMode {
		fmt.Println("\n--- Running ai-suggestor.py for Sensitive PDF Suggestion ---")
		fmt.Println("Potential sensitive PDFs will be saved to suggestion.txt")
		fmt.Println("Note: Using concurrency may prevent the script from stopping immediately with Ctrl+C.")
		fmt.Println("For easier stopping with Ctrl+C, choose 'no' for concurrency.")

		// Prompt for Concurrency
		fmt.Print("Do you want to use concurrency in ai-suggestor.py? (yes/no): ")
		concurrencyInput, _ := reader.ReadString('\n')
		concurrencyChoice = strings.TrimSpace(strings.ToLower(concurrencyInput))
		if concurrencyChoice != "yes" && concurrencyChoice != "y" {
			concurrencyChoice = "no"
		} else {
			concurrencyChoice = "yes"
		}

		// **NEW**: Prompt for AI Model Choice
		fmt.Println("\n--- Choose AI Model for Python Script ---")
		fmt.Println("The Python script needs to know which AI model to use.")
		fmt.Println("Available options (ensure corresponding .env vars are set in Python):")
		fmt.Println("1: Gemini")
		fmt.Println("2: Anthropic")
		fmt.Println("3: OpenAI")
		for { // Loop until valid input
			fmt.Print("Enter your choice (1, 2, or 3): ")
			modelInput, _ := reader.ReadString('\n')
			aiModelChoice = strings.TrimSpace(modelInput)
			if aiModelChoice == "1" || aiModelChoice == "2" || aiModelChoice == "3" {
				break // Valid choice
			}
			fmt.Println("Invalid input. Please enter 1, 2, or 3.")
		}
		fmt.Printf("Selected AI Model for Python script: %s\n", aiModelChoice)

		startTimeAI := time.Now()
		// Pass necessary args: script, input file, concurrency, model choice
		err := runPythonScript("ai-suggestor.py", outputPath, concurrencyChoice, aiModelChoice)
		if err != nil {
			log.Printf("Error executing ai-suggestor.py: %v", err)
			// Consider if this should be fatal depending on requirements
		} else {
			fmt.Printf("ai-suggestor.py finished execution.\n")
		}
		endTimeAI := time.Now()
		durationAI := endTimeAI.Sub(startTimeAI)
		fmt.Printf("ai-suggestor.py execution duration: %s\n", durationAI)
		fmt.Println("Check suggestion.txt for potential sensitive PDFs.")
	}

	// --- Final Messages ---
	if !his200Mode && !fetchPDFs && !aiMode {
		fmt.Println("\nInitial fetch complete. Filtered URLs saved to filtered_output.txt")
		fmt.Println("Use -his200 flag to automatically perform 200 status check (saves to archived200.txt).")
		fmt.Println("Use -his200 -su flags to check 200 status for a single selected URL (can check multiple).")
		fmt.Println("Use -pdf flag to automatically run sort-keywords.py for PDF scanning (saves to sorted-keywords.txt).")
		fmt.Println("Use -ai flag to automatically run ai-suggestor.py for sensitive PDF suggestion (saves to suggestion.txt).")
	}

	// --- End total program time ---
	endTimeTotal := time.Now()
	totalProgramDuration := endTimeTotal.Sub(startTime) // Use the overall start time
	fmt.Printf("\nTotal program duration: %s\n", totalProgramDuration)
}

// Helper function to read URLs from a file
func readURLsFromFile(filePath string) ([]string, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("error opening file %s: %w", filePath, err)
	}
	defer file.Close()

	var urls []string
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line != "" { // Only add non-empty lines
			urls = append(urls, line)
		}
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("error reading file %s: %w", filePath, err)
	}

	return urls, nil
}

// check200Archives processes a list of URLs to find their archived versions with status 200
func check200Archives(urls []string, fileWriter io.Writer) {
	totalFound := 0
	for _, urlPattern := range urls {
		fmt.Fprintf(os.Stderr, "Checking archives for: %s%s%s\n", ColorYellow, urlPattern, ColorReset)
		foundCount := getWayback200URLs(urlPattern, fileWriter)
		if foundCount > 0 {
			fmt.Fprintf(os.Stderr, "  Found %d archived 200 links.\n", foundCount)
			totalFound += foundCount
		} else {
			fmt.Fprintf(os.Stderr, "  No archived 200 links found.\n")
		}
	}
	fmt.Fprintf(os.Stderr, "\nFinished 200 check. Total archived links found: %d\n", totalFound)
	fmt.Fprintln(os.Stderr, strings.Repeat("-", 50))
}

// getWayback200URLs queries the Wayback Machine CDX API for a single URL pattern with status code 200
func getWayback200URLs(urlPattern string, fileWriter io.Writer) int {
	cdxAPIURL := "http://web.archive.org/cdx/search/cdx"
	params := url.Values{}
	params.Add("url", urlPattern)
	params.Add("filter", "statuscode:200")
	params.Add("fl", "timestamp,original")
	params.Add("output", "json")
	requestURL := cdxAPIURL + "?" + params.Encode()

	// Add a small delay to be slightly nicer to the API
	time.Sleep(200 * time.Millisecond)

	client := http.Client{Timeout: 45 * time.Second} // Increased timeout slightly
	resp, err := client.Get(requestURL)
	if err != nil {
		fmt.Fprintf(os.Stderr, "  %sError making HTTP request for %s: %v%s\n", ColorRed, urlPattern, err, ColorReset)
		return 0
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		fmt.Fprintf(os.Stderr, "  %sError reading response body for %s: %v%s\n", ColorRed, urlPattern, err, ColorReset)
		return 0
	}

	if resp.StatusCode != http.StatusOK {
		// Log non-200 status but don't treat as fatal error for this specific URL check
		fmt.Fprintf(os.Stderr, "  %sReceived non-200 status (%d) for %s%s\n", ColorYellow, resp.StatusCode, urlPattern, ColorReset)
		return 0
	}

	var data [][]string
	// Handle empty response body which causes Unmarshal error
	if len(body) == 0 {
		// fmt.Fprintf(os.Stderr, "  Received empty response body for %s\n", urlPattern)
		return 0 // No data
	}
	err = json.Unmarshal(body, &data)
	if err != nil {
		// Log JSON decoding errors, potentially indicating API issues or unexpected format
		fmt.Fprintf(os.Stderr, "  %sError decoding JSON response for %s: %v%s\n", ColorRed, urlPattern, err, ColorReset)
		// fmt.Fprintf(os.Stderr, "  Response body was: %s\n", string(body)) // Optional: log body on error
		return 0
	}

	// Check if data is empty or doesn't have the expected header + records structure
	if len(data) < 2 || len(data[0]) == 0 {
		// fmt.Fprintf(os.Stderr, "  No 200 records found in JSON response for %s\n", urlPattern)
		return 0
	}

	records := data[1:] // Actual data records start from the second element
	fields := data[0]   // Header row defining fields
	timestampIndex, originalIndex := -1, -1
	for i, field := range fields {
		if field == "timestamp" {
			timestampIndex = i
		} else if field == "original" {
			originalIndex = i
		}
	}

	// Check if the required fields were found in the header
	if timestampIndex == -1 || originalIndex == -1 {
		fmt.Fprintf(os.Stderr, "  %sError: Required fields ('timestamp', 'original') not found in API response header for %s%s\n", ColorRed, urlPattern, ColorReset)
		fmt.Fprintf(os.Stderr, "  Header received: %v\n", fields) // Log the header
		return 0
	}

	resultsCount := 0
	for _, record := range records {
		// Ensure the record has enough elements to access the required indices
		if len(record) > timestampIndex && len(record) > originalIndex {
			timestamp := record[timestampIndex]
			originalURL := record[originalIndex]
			// Basic validation of timestamp format (digits only)
			if _, err := strconv.ParseInt(timestamp, 10, 64); err == nil {
				waybackURL := fmt.Sprintf("https://web.archive.org/web/%s/%s", timestamp, originalURL)
				// Print to stdout for user visibility
				fmt.Fprintf(os.Stdout, "  Found 200 link: %s%s%s\n", ColorCyan, waybackURL, ColorReset)
				// Write to the output file
				_, writeErr := fmt.Fprintf(fileWriter, "%s\n", waybackURL)
				if writeErr != nil {
					// Log error writing to file but continue processing other records
					log.Printf("Error writing URL %s to file: %v", waybackURL, writeErr)
				} else {
					resultsCount++
				}
			} else {
				// Log if timestamp format is unexpected
				fmt.Fprintf(os.Stderr, "  %sSkipping record for %s due to invalid timestamp format: %s%s\n", ColorYellow, urlPattern, timestamp, ColorReset)
			}
		} else {
			// Log if a record has fewer fields than expected based on the header
			fmt.Fprintf(os.Stderr, "  %sSkipping malformed record for %s: %v%s\n", ColorYellow, urlPattern, record, ColorReset)
		}
	}
	return resultsCount
}

// Helper function to find the minimum of two integers
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// Helper function to create an empty archived200.txt file
func createEmptyArchived200File() {
	archived200Path := "archived200.txt"
	file, err := os.Create(archived200Path)
	if err != nil {
		log.Printf("Warning: Could not create empty %s file: %v", archived200Path, err)
	} else {
		// Close the file immediately after creating it
		file.Close()
		fmt.Printf("Created empty %s file as no URLs were found or selected for 200 check.\n", archived200Path)
	}
}

// runPythonScript runs a Python script using the appropriate interpreter based on OS
// **MODIFIED**: Added aiModelChoice argument and corrected interpreter selection logic
func runPythonScript(scriptPath, inputFile, useConcurrency, aiModelChoice string) error {
	fmt.Printf("Attempting to run Python script %s with input %s, concurrency %s", scriptPath, inputFile, useConcurrency)
	if aiModelChoice != "" {
		fmt.Printf(", model choice %s", aiModelChoice)
	}
	fmt.Println("...")

	var interpreter string
	osName := runtime.GOOS // Get the operating system name

	// **CORRECTED LOGIC**: Select interpreter based on OS
	if osName == "windows" {
		// On Windows, prioritize 'python'
		_, errPy := exec.LookPath("python")
		if errPy == nil {
			interpreter = "python"
		} else {
			// Fallback to check 'python3' on Windows (less common)
			_, errPy3 := exec.LookPath("python3")
			if errPy3 == nil {
				interpreter = "python3"
			} else {
				return fmt.Errorf("could not find 'python' or 'python3' executable in PATH on Windows")
			}
		}
	} else {
		// On non-Windows (Linux, macOS, etc.), prioritize 'python3'
		_, errPy3 := exec.LookPath("python3")
		if errPy3 == nil {
			interpreter = "python3"
		} else {
			// Fallback to check 'python' on non-Windows
			_, errPy := exec.LookPath("python")
			if errPy == nil {
				interpreter = "python"
			} else {
				return fmt.Errorf("could not find 'python3' or 'python' executable in PATH on %s", osName)
			}
		}
	}

	log.Printf("Using interpreter: %s for OS: %s", interpreter, osName)

	// Construct arguments for the command
	args := []string{scriptPath, inputFile, useConcurrency}
	if aiModelChoice != "" {
		args = append(args, aiModelChoice) // Add model choice if provided
	}

	// Create the command
	cmd := exec.Command(interpreter, args...)
	cmd.Stdout = os.Stdout // Pipe Python's stdout to Go's stdout
	cmd.Stderr = os.Stderr // Pipe Python's stderr to Go's stderr
	// Do NOT set cmd.Stdin = os.Stdin

	// Run the command and wait for it to finish
	err := cmd.Run()
	if err != nil {
		// Log the error, including the exit status if available
		log.Printf("Error executing %s with %s: %v", scriptPath, interpreter, err)
		// Return a more specific error including the script path and interpreter
		return fmt.Errorf("failed to run Python script %s with %s: %w", scriptPath, interpreter, err)
	}

	// Log successful execution
	fmt.Printf("Python script %s finished successfully using %s.\n", scriptPath, interpreter)
	return nil // Indicate success
}
