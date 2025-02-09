import os

def matches_keywords(line, keywords):
    """
    Returns True if 'line' contains at least one of the provided keywords.
    If 'keywords' is empty, returns True (no filtering).
    """
    if not keywords:
        return True
    lower_line = line.lower()
    return any(kw.lower() in lower_line for kw in keywords)

def get_last_line_of_file(file_path):
    """
    Safely reads the last non-empty line of 'file_path'.
    Returns None if the file doesn't exist or all lines are blank.
    """
    if not os.path.isfile(file_path):
        return None

    last_line = None
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            text = line.strip()
            if text:
                last_line = text
    return last_line

def skip_to_domain(infile, start_domain):
    """
    Reads lines from 'infile' until a line.strip() matches 'start_domain'.
    Returns True once the domain is found, False if EOF is reached without finding it.
    When True is returned, the file handle is positioned right after the matching line.
    """
    if not start_domain:
        return True  # No skipping needed

    while True:
        position = infile.tell()
        line = infile.readline()
        if not line:
            # Reached end of file without finding domain
            return False
        if line.strip() == start_domain.strip():
            # Found the domain; we're now just past it
            return True

def single_pass_filtering(
    file_path, start_domain, protocol, keywords, infinity_count
):
    """
    If user chooses to skip splitting (num_files=0 or blank),
    we only do filtering + optional Infinity collection in a single pass.

    - 'infinity_count' can be:
        * An integer (e.g., 100) for partial collection.
        * None for unlimited collection if the user chose 'i'.
    """
    base_name, ext = os.path.splitext(file_path)

    # Set up Infinity file if requested
    infinity_file = None
    infinity_file_path = None
    infinity_collected = 0

    # If infinity_count is not 0, user wants Infinity
    # If it's None, that means unlimited Infinity
    if infinity_count is not None and infinity_count > 0:
        infinity_file_path = f"{base_name}_infinity{ext}"
        infinity_file = open(infinity_file_path, "w", encoding="utf-8")
    elif infinity_count is None:
        # infinity_count=None => unlimited Infinity
        infinity_file_path = f"{base_name}_infinity{ext}"
        infinity_file = open(infinity_file_path, "w", encoding="utf-8")

    with open(file_path, "r", encoding="utf-8", errors="ignore") as infile:
        # If start_domain is provided, skip lines up to that domain
        if start_domain:
            print(f"Skipping lines until we find domain: {start_domain}")
            found = skip_to_domain(infile, start_domain)
            if not found:
                print("Could not find the starting domain in the main file. No lines processed.")
                if infinity_file:
                    infinity_file.close()
                return

        # Now filter lines onward
        lines_processed = 0
        for line in infile:
            if matches_keywords(line, keywords):
                processed_line = f"{protocol}://{line.strip()}\n"
                lines_processed += 1

                # If Infinity is open, write lines until we hit the limit (or indefinitely if None)
                if infinity_file:
                    if infinity_count is None:
                        # 'i' mode => no limit
                        infinity_file.write(processed_line)
                        infinity_collected += 1
                    else:
                        # integer mode
                        if infinity_collected < infinity_count:
                            infinity_file.write(processed_line)
                            infinity_collected += 1

    if infinity_file:
        infinity_file.close()

    print(f"\n--- Single-Pass Filtering Complete ---")
    print(f"Total matching lines (after '{start_domain}' if provided): {lines_processed}")
    if infinity_file_path and (infinity_collected > 0 or infinity_count is None):
        count_str = f"(collected {infinity_collected} lines)" if infinity_count is not None else "(unlimited mode)"
        print(f"Infinity file created: {infinity_file_path} {count_str}")

def two_pass_splitting(
    file_path, start_domain, num_files, protocol, keywords, infinity_count
):
    """
    Two-pass approach for splitting:
      1) First pass: Count matching lines (after skipping to 'start_domain') to
         determine how many lines per file.
      2) Second pass: Again skip to 'start_domain', then distribute lines among
         split files. Simultaneously handle Infinity if needed.

    - 'infinity_count' can be:
        * An integer => partial Infinity
        * None => unlimited Infinity
        * 0 => skip Infinity
    """
    base_name, ext = os.path.splitext(file_path)

    # --- FIRST PASS: Count matching lines after skipping ---
    print("First pass: counting matching lines...")
    total_matched = 0
    with open(file_path, "r", encoding="utf-8", errors="ignore") as infile:
        # Skip lines up to the domain if provided
        if start_domain:
            print(f"Skipping lines until we find domain: {start_domain}")
            found = skip_to_domain(infile, start_domain)
            if not found:
                print("Could not find the starting domain in the main file. No lines processed.")
                return

        for line in infile:
            if matches_keywords(line, keywords):
                total_matched += 1

    if total_matched == 0:
        print("No matching lines found. Nothing to split.")
        return

    print(f"Found {total_matched} matching lines.\n")

    # Calculate distribution
    lines_per_file = total_matched // num_files
    remainder = total_matched % num_files

    print(f"Splitting into {num_files} file(s) ...")
    print(f"~{lines_per_file} lines in each file (+1 in {remainder} file(s) to handle remainder)\n")

    # --- Prepare Infinity file if requested ---
    infinity_file = None
    infinity_file_path = None
    infinity_collected = 0

    if infinity_count is not None and infinity_count > 0:
        infinity_file_path = f"{base_name}_infinity{ext}"
        infinity_file = open(infinity_file_path, "w", encoding="utf-8")
    elif infinity_count is None:
        # 'i' => unlimited Infinity
        infinity_file_path = f"{base_name}_infinity{ext}"
        infinity_file = open(infinity_file_path, "w", encoding="utf-8")

    # --- SECOND PASS: Distribute lines ---
    current_file_index = 1
    lines_in_current_file = 0
    remainder_used = 0
    if remainder > 0:
        lines_for_this_file = lines_per_file + 1
        remainder_used = 1
    else:
        lines_for_this_file = lines_per_file

    out_file_path = f"{base_name}_split_{current_file_index}{ext}"
    outfile = open(out_file_path, "w", encoding="utf-8")

    with open(file_path, "r", encoding="utf-8", errors="ignore") as infile:
        # Skip lines up to the domain if provided
        if start_domain:
            found = skip_to_domain(infile, start_domain)
            if not found:
                print("Could not find the starting domain in the main file during second pass.")
                outfile.close()
                if infinity_file:
                    infinity_file.close()
                return

        matched_count = 0
        for line in infile:
            if matches_keywords(line, keywords):
                matched_count += 1
                processed_line = f"{protocol}://{line.strip()}\n"

                # Write to current split file
                outfile.write(processed_line)
                lines_in_current_file += 1

                # Infinity logic
                if infinity_file:
                    if infinity_count is None:
                        # 'i' => unlimited
                        infinity_file.write(processed_line)
                        infinity_collected += 1
                    else:
                        if infinity_collected < infinity_count:
                            infinity_file.write(processed_line)
                            infinity_collected += 1

                # Move to next file if this one is full
                if lines_in_current_file >= lines_for_this_file:
                    outfile.close()
                    current_file_index += 1
                    if current_file_index > num_files:
                        # We have filled all split files
                        break

                    out_file_path = f"{base_name}_split_{current_file_index}{ext}"
                    outfile = open(out_file_path, "w", encoding="utf-8")

                    lines_in_current_file = 0
                    if remainder_used < remainder:
                        lines_for_this_file = lines_per_file + 1
                        remainder_used += 1
                    else:
                        lines_for_this_file = lines_per_file

    # Close open files
    if not outfile.closed:
        outfile.close()
    if infinity_file:
        infinity_file.close()

    print("--- Splitting Complete ---")
    print(f"Total matching lines distributed: {total_matched}")
    for i in range(1, current_file_index + 1):
        split_file_name = f"{base_name}_split_{i}{ext}"
        if os.path.exists(split_file_name):
            print(f"Created: {split_file_name}")

    if infinity_file_path:
        if infinity_count is None:
            print(f"Infinity file created: {infinity_file_path} (unlimited mode: {infinity_collected} lines)")
        elif infinity_collected > 0:
            print(f"Infinity file created: {infinity_file_path} (collected {infinity_collected} lines)")

def main():
    print("============================================")
    print("       Welcome to the Enhanced Splitter     ")
    print("============================================\n")

    # 1) Prompt user for the main file path
    file_path = input("Enter the full path of the main file containing all domains: ").strip()
    if not os.path.isfile(file_path):
        print("Main file not found. Exiting...")
        return

    # 2) Optionally ask user for a "previous filtered file" to skip lines
    prev_filtered_path = input(
        "Enter the path of your previous filtered file to continue from its last domain (leave blank to skip): "
    ).strip()

    start_domain = None
    if prev_filtered_path:
        # Read the last line of that file
        start_domain = get_last_line_of_file(prev_filtered_path)
        if start_domain:
            print(f"Last domain found in '{prev_filtered_path}': {start_domain}")
        else:
            print(f"Could not read a valid last line from '{prev_filtered_path}'. Continuing without skipping.")
            start_domain = None

    # 3) Ask the user for number of split files
    #    If user presses Enter or enters 0, we skip splitting
    num_files_input = input(
        "How many split files do you want to create? (Enter 0 or leave blank to skip splitting): "
    ).strip()
    skip_splitting = False
    num_files = 0
    if not num_files_input:  # user pressed Enter with no input
        skip_splitting = True
    else:
        try:
            num_files = int(num_files_input)
            if num_files <= 0:
                skip_splitting = True
        except ValueError:
            skip_splitting = True

    # 4) Ask user which protocol they'd like to prepend
    protocol_choice = input("Choose protocol to prepend [http or https]: ").strip().lower()
    if protocol_choice not in ("http", "https"):
        print("Invalid or no protocol choice. Defaulting to https...")
        protocol_choice = "https"

    # 5) Ask user for keywords (comma-separated). If empty, no keyword filtering
    keywords_input = input("Enter keyword(s) to filter lines (comma-separated). Leave blank for no filtering: ").strip()
    if keywords_input:
        keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
    else:
        keywords = []

    # 6) Infinity scan - can be integer, 0, or 'i' for unlimited
    infinity_input = input(
        "Infinity Scan: How many matching lines in 'infinity' file? (Enter 0 to skip, or 'i' for unlimited): "
    ).strip().lower()

    # Interpret infinity input
    if infinity_input == 'i':
        # 'i' => unlimited Infinity
        infinity_count = None
    else:
        # Try to parse an integer, default 0 if invalid
        try:
            infinity_count = int(infinity_input or "0")
        except ValueError:
            infinity_count = 0
        if infinity_count < 0:
            infinity_count = 0

    # 7) Perform the work
    if skip_splitting:
        # Just filter + (optionally) do Infinity
        print("\nSkipping file splitting. Proceeding with single-pass filtering...\n")
        single_pass_filtering(
            file_path=file_path,
            start_domain=start_domain,
            protocol=protocol_choice,
            keywords=keywords,
            infinity_count=infinity_count
        )
    else:
        # Two-pass approach for splitting + Infinity
        two_pass_splitting(
            file_path=file_path,
            start_domain=start_domain,
            num_files=num_files,
            protocol=protocol_choice,
            keywords=keywords,
            infinity_count=infinity_count
        )

if __name__ == "__main__":
    main()
