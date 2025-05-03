

🚀 Project Name : del-packURLs
===============

![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-purple.svg)
</a><a href="https://github.com/gigachad80/del-packURLs/issues"><img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat"></a>

#### del-packURLs : Automates the process of Information Disclosure Vulnerability Discovery 


### 📌 Overview

    *_del-packURLs_* web security automation tool designed to enhance information disclosure vulnerability discovery, particularly in bug hunting scenarios. It streamlines the process of extracting potentially sensitive files and information. The tool leverages the Wayback Machine CDX API to retrieve archived URLs for a given target domain, filtering for specific file extensions (e.g., apk, dll, exe, json, txt, pdf, zip etc...).  A key feature is its ```200 History Mode```,' which identifies when these files were accessible with a 200 OK status code, addressing the challenge of locating resources that are currently unavailable (404 Page Not Found). This automation aims to improve efficiency for bug hunters by providing direct terminal access to this historical data, common for Linux users.  Furthermore, the tool can integrate with AI models (Gemini, Claude, GPT) to provide intelligent suggestions on potentially sensitive PDF files. The tool also provides functionality to use concurrency." 

### 🙃Why I created this

   The main reason for developing this was so that pentesters could efficiently perform the maximum number of information disclosure vulnerability finding tasks from the terminal. When I watched Lossec's video (or rather, I saw this reel first, then watched Lossec's video a few months later, and even observed some bug hunters), I noticed that most people perform these tasks manually instead of using the terminal. What kind of Linux user abandons the terminal to work manually? Also, I saw that when both encounter a '404 Page not found' error, they manually go to each link and enter it into the web archive to see when it was live (200 Status OK). With so many links, the user won't understand which one is good and sensitive, so I developed a solution where it fetches from the terminal, shows live archived links from the terminal itself, and provides AI recommendation of sensitive PDFs . I know that people can fetch using the curl command, but I used Golang to make it a bit faster. One thing to note here is that if the internet speed is fast while fetching with curl and slow while using Go, curl's result will come sooner, even though Go has good performance. But I thought, why use curl when I have the standard library? Performance + Fast Internet Speed 🗿


### 📚  Requirements & Dependencies

* #### Golang
* #### Python 3 

### 📥 Installation Guide & Usage 

 1. Git clone the repo : 
```
git clone https://github.com/gigachad80/del-packURLs
```
 2. Go to del-packURLs directory and give permission to main.go or you can directly build from the source ( go build ```del-packURLs.go``` )
 3. Run command ```./del-packURLs.go``` . Please note that either you can use whole syntax like this
 -  ``` ./del-packURLs -domain example.com ---- and rest of flags```
  or just type the command 
 - ```./del-packURLs``` and it'll ask for domain & extension . Enter your target domain/URL and flags and run it . 

 4. For help or menu guide  , enter ```del-packURLs.go -h```



### 🤨 How it is different from grep-backURLs ?

| grep-backURLs  | del-packURLs |
| ------------- |:-------------:|
| Uses keyword from keyword.txt to find sensitive data    | Uses Wayback CDX API and pre-defined keywords to find sensitive files    |
| Finds all URLs     | Finds only files    |
| Does not Use AI      | Use AI models like Gemini , Claude , GPT to suggest sensitive PDFs for analysis   |

#### Fun Fact : I developed both of them.🤓 My Repo for grep-backURLs: [Repo link](https://github.com/gigachad80/grep-backURLs)

### 📝 Roadmap / To-do 

- [ ] Add ```-load``` flag in syntax .
- [ ] Update README.md with Demo sntax to use
- [ ] Add ```Back to Main Menu``` functionality 
- [ ] Add more keywords for in ```sort-keywords.py``` for sensitive docs . 
- [ ] Support for Virustotal & Alienvault to fetch URLs just like CDX API.
- [ ] Not sure but if possible, I'll integrate AI file analysis ( for image , text , pdf etc...)


### Notes to be Taken / Imp. Points . 


<div style="border-left: 4px solid #3B82F6; background-color: #EFF6FF; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
  <p style="margin-top: 0; margin-bottom: 10px; color: #1E3A8A; font-weight: bold;">
    <svg aria-hidden="true" viewBox="0 0 16 16" version="1.1" width="16" height="16" data-view-component="true" style="display: inline-block; vertical-align: text-bottom; fill: currentColor;">
      <path d="M8 1.5c3.6 0 6.5 2.9 6.5 6.5s-2.9 6.5-6.5 6.5S1.5 11.6 1.5 8 4.4 1.5 8 1.5zM8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0zm.75 7.75V4.25a.75.75 0 0 0-1.5 0v3.5a.75.75 0 0 0 .75.75h.75v-.75zm0 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5z"></path>
    </svg>
    Note
  </p>
  <ul style="margin-top: 0; margin-bottom: 0; color: #1E3A8A; padding-left: 20px;">
    <li> PDF Suggestion & Analysis: AI will only recommend sensitive PDF while PyMuPDF will analyze it.
    </li>
    <li>Decode URLs:Check go file line 219 if you need decoded URLs to fetch.'.</li>
    <li>Requirements txt : pip installs all AI models by default , so if you wnt to use single AI model , then install only that.'.</li>
    <li>Modify prompt : Check line 106 of <code>ai-suggestor.py</code> in to modify the prompt for suggestions.'.</li>
    <li>Python : It uses <code>python</code> for Windows & <code>python3</code> for Linux'.</li>
    <li> AI testing: I have only tested Gemini so far, because ChatGPT and Claude's API keys are not free, that's why 
    </li>
    <li>Starting Download: Script shows "Downloading: [URL]" first.</li>
    <li>File Not Found: "Not Found (404): [URL]" means URL is broken/removed.</li>
    <li>Download Error: "Error downloading [URL]: [error details]" indicates a network issue.</li>
    <li>PDF Processing Error: "Error processing PDF [URL]: [error]" means file isn't a valid PDF. Even if it's PDF, PyMuPDF lib. won't be unable to analyse that.</li>
    <li>No Keywords: "No sensitive keywords found in: [URL]" means PDF text lacks defined terms.</li>
    <li>Keywords Found: "Found keywords: [keywords] in [URL]" means terms were detected in PDF.</li>
    <li>Keyword Found Color: Green output indicates keywords were successfully found.</li>
    <li>Error Colors: Red output signals download or processing errors.</li>
    <li>Ctrl+C with Concurrency: Ctrl+C will not stop immediately with concurrency (esp. with <code>sort-keywords.py</code>). It'll process & analyze all PDF then.</li>
    <li>Output File: Sensitive URLs with keywords saved to 'sorted-keywords.txt'.</li>
  </ul>
</div>

<div style="border-left: 4px solid #22C55E; background-color: #F0FDF4; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
  <p style="margin-top: 0; margin-bottom: 10px; color: #166534; font-weight: bold;">
    <svg aria-hidden="true" viewBox="0 0 16 16" version="1.1" width="16" height="16" data-view-component="true" style="display: inline-block; vertical-align: text-bottom; fill: currentColor;">
      <path d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8zm8-6.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13zM7 6.75A.75.75 0 0 1 7.75 6h.5a.75.75 0 0 1 .75.75v1.5h.25a.75.75 0 0 1 0 1.5H8.5a.75.75 0 0 1-.75-.75V8.25h-.25a.75.75 0 0 1 0-1.5zM8 10.5a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"></path>
    </svg>
    Tip
  </p>
  <ul style="margin-top: 0; margin-bottom: 0; color: #166534; padding-left: 20px;">
    <li>Concurrency Impact: Concurrency ("yes" flag) can speed up checks.</li>
    <li>Use grep for sorting Found Keyword(s) from <code>sorted-keywords.txt</code> file.</li>
  </ul>
</div>


### 🤔 Why This Name?

 First, I decided to use both the Web Archive CDX API and [Waybackpack](https://github.com/jsvine/waybackpack) (one for fetching and one for showing the 200 status of archived URLs). However, after trying a lot, Waybackpack didn't work. Then, one day, an idea suddenly came to me: why not just do it normally using the CDX API, which would show timestamps, status codes, and URLs? After modifying it a bit, it easily showed all the archived URLs that once had a 200 OK status code but are currently 404. So, even though I didn't end up using Waybackpack, it was my initial approach. And ```del``` refers to deleted (404 Page not found). So, I named it del-packURLs.

### ⌚ Total Time taken in development , testing , trying diferent approaches & variations , debugging , even writing README. 

 Approx 17 hr 47 min 

### 💓 Credits:

  I extend my sincere gratitude to Wesley Hill for creating video This project simply wouldn't exist if they hadn't created it.
  
  - [Lossec aka CoffinXP](https://youtu.be/ND_0l-lpmf8?si=v9WGjhmlP4ZlMd1Q) and his video for inspiration.  
  - [ IHA 089 ](https://www.instagram.com/reel/DGNtxGGB8gN/?igsh=MWw1YWN4Y3JmcjQ5aw==) for IG Reel




### 📞 Contact


 📧 Email: pookielinuxuser@tutamail.com


### 📄 License

Licensed under **GNU General Public License v3.0**

🕒 Last Updated: April 3, 2025 

