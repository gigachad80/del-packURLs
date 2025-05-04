
# Contributing to del-packURLs

We're thrilled that you're interested in contributing to `del-packURLs`! Your help is valuable in making this tool more robust, efficient, and useful for information disclosure vulnerability discovery.

This document outlines the guidelines and processes for contributing to the project.


## How to Contribute

There are several ways you can contribute to `del-packURLs`:

1.  **Reporting Bugs:** If you find a bug or unexpected behavior, please let us know!
2.  **Suggesting Enhancements or New Features:** Have an idea for a new feature or an improvement to existing functionality? We'd love to hear it.
3.  **Contributing Code:** Help fix bugs, implement new features, or improve the existing codebase.
4.  **Adding Sensitive Keywords:** Contribute to the list of keywords used for identifying sensitive information, particularly in PDFs.
5.  **Improving Documentation:** Help improve the README, contributing guide, or other documentation.

We use GitHub Issues and Pull Requests to manage contributions.

### Reporting Bugs

If you encounter a bug, please open a new issue on the GitHub repository. To help us understand and fix the issue quickly, please include:

* A clear and descriptive title.
* Steps to reproduce the bug.
* Expected behavior.
* Actual behavior.
* Your operating system and Go/Python versions.
* Any relevant error messages or output.

### Suggesting Enhancements or New Features

Have an idea that could make `del-packURLs` better? Please open a new issue on GitHub to propose it. When suggesting a feature, please describe:

* The proposed feature or enhancement.
* Why it would be useful.
* How it might work (if you have specific ideas).
* Any alternatives you've considered.

### Contributing Code

If you want to contribute code to fix a bug or implement a feature (either one you suggested or from the roadmap), please follow these steps:

1.  **Fork the Repository:** Click the "Fork" button on the top right of the `del-packURLs` GitHub page.
2.  **Clone Your Fork:** Clone your forked repository to your local machine:
    ```bash
    git clone [https://github.com/gigachad80/del-packURLs.git](https://github.com/gigachad80/del-packURLs.git)
    cd del-packURLs
    ```

4.  **Make Your Changes:** Write your code! Ensure you follow the existing code style for both Go and Python parts of the project.
5.  **Test Your Changes:** If you are fixing a bug or adding a feature, please test your changes thoroughly.
6.  **Commit Your Changes:** Commit your changes with a clear and concise commit message. A good commit message often includes a brief summary, followed by a more detailed explanation if needed.
    ```bash
    git commit -m "feat: Add cool new feature"
    ```
7.  **Push Your Changes:** Push your branch to your forked repository on GitHub:
    ```bash
    git push origin your-new-branch-name
    ```
8.  **Create a Pull Request (PR):** Go to the original `del-packURLs` repository on GitHub. You should see a banner prompting you to create a pull request from your recently pushed branch. Click on it and fill out the PR template. Link the PR to any relevant issues (e.g., "Closes #123" or "Fixes #456").

Your PR will be reviewed, and feedback may be provided. We appreciate your patience during this process.

### Adding Sensitive Keywords

The AI suggestion and PDF analysis features rely on a list of sensitive keywords. You can contribute by adding new keywords that are relevant for identifying potentially sensitive information.

1.  Locate the file where the sensitive keywords are stored (based on the project structure, this is likely related to `sort-keywords.py` or a configuration file it uses).
2.  Fork the repository and create a new branch as described in the "Contributing Code" section above.
3.  Add your new keywords to the relevant file, following the existing format.
4.  Test locally if possible to ensure your additions don't cause errors.
5.  Commit your changes and push your branch.
6.  Open a Pull Request, clearly stating which keywords you added and why they are relevant.

### Improving Documentation

Clear documentation is crucial for users. If you find typos, confusing explanations, or areas where more detail is needed in the README or other project files, please feel free to submit a Pull Request with your improvements.

## Development Setup

To contribute code, you will need:

* [Golang](https://golang.org/dl/) installed.
* [Python 3](https://www.python.org/downloads/) installed.
* The project dependencies installed (e.g., using `pip install -r requirements.txt`).

Refer to the main `README.md` for detailed installation and setup instructions.

## Pull Request Guidelines

* Ensure your code adheres to the project's existing style.
* Write clear and concise commit messages.
* Link your PR to any related issues.
* Be prepared to address feedback during the review process.
* Keep PRs focused on a single issue or feature.

## Thank You!

Thank you for considering contributing to `del-packURLs`. Your efforts help make this tool better for the entire community!
