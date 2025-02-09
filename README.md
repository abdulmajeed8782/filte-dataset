# Enhanced Splitter Script

This Python script offers a powerful and flexible way to filter, split, and prepend protocols to lines in a massive text file—perfect for handling large sets of domain data. Plus, you can easily continue from where you left off in a previous run and create an unlimited “infinity” file to capture all matching lines.

## Features

1. **Optional Splitting**  
   - Prompt for a number of output files. If you enter `0` or leave blank, splitting is skipped.

2. **Continue From a Previous File**  
   - Provide a path to a previously filtered file. The script reads the **last line** of that file, finds that domain in the main file, and starts processing from the **next** line forward.

3. **Keyword Filtering**  
   - Enter one or more comma-separated keywords. Only lines containing at least one keyword are kept.  
   - Leave blank to keep all lines.

4. **Protocol Prepending**  
   - Choose `http` or `https` to prepend to each matching line, e.g., transforms `example.com` into `https://example.com`.

5. **Infinity Scan**  
   - Specify a number of matching lines to collect in a special `_infinity.txt` file.  
   - Enter `0` to skip Infinity, or **`i`** for unlimited Infinity, capturing **all** matched lines in one file.

6. **Large File Handling**  
   - Reads the file line by line to keep memory usage low.  
   - Optionally performs a two-pass split:
     1. **First Pass**: Counts matching lines.
     2. **Second Pass**: Actually writes those lines into the desired number of files.

## How It Works

1. **User Prompts**  
   - **Main File Path**: Points to your large text file containing domains.  
   - **Previous Filtered File** (optional): Tells the script where to resume from; it scans for the last domain in that file, then finds it in the main file.  
   - **Number of Split Files**: Leave blank or enter `0` to skip splitting.  
   - **Protocol**: Either `http` or `https`.  
   - **Keywords**: Comma-separated list of filters (leave blank for all).  
   - **Infinity Mode**:  
     - Enter a number (e.g., `500`) to collect that many lines, or  
     - Enter `0` to skip, or  
     - Enter `i` to capture **all** matched lines.

2. **Single-Pass vs. Two-Pass**  
   - **Single-Pass**: If splitting is skipped, the script processes the file once, optionally creating an infinity file.  
   - **Two-Pass**: If you choose splitting, the script performs:  
     1. **Counting Pass** – determines how many lines match the keywords.  
     2. **Splitting Pass** – distributes those lines across the requested number of files, creating an infinity file if requested.

## Usage

1. **Install/Run**  
   - Requires **Python 3.6+** (no external libraries needed).  
   - Run in a terminal:  
     ```bash
     python enhanced_splitter.py
     ```
2. **Follow the Prompts**  
   - Enter your file paths, number of splits, protocol, keywords, and Infinity settings.  
3. **Check the Output**  
   - If splitting: files named `[filename]_split_1.txt`, `[filename]_split_2.txt`, etc.  
   - If Infinity is enabled: a file named `[filename]_infinity.txt`, containing either the specified number of lines or **all** matching lines (if you used the `i` option).

## Example

- **Main file**: `alldomains.txt`  
- **Previously filtered file**: `filtered_1.txt`  
- **Number of split files**: `3`  
- **Protocol**: `https`  
- **Keywords**: `edu, school, college`  
- **Infinity**: `i` (unlimited)  

When prompted, you’d enter:
