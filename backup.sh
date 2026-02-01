#!/usr/bin/env fish

# Iterate over all files in the current directory ending with .py
for file in *.py
    # Construct the new filename by appending .bak to the original filename
    set bak_file "$file.bak"

    # Check if the backup file already exists to prevent overwriting without warning
    if test -e "$bak_file"
        echo "Skipping: $bak_file already exists."
    else
        # Copy the original file to the new backup file name
        cp "$file" "$bak_file"
        echo "Backed up: $file to $bak_file"
    end
end
