import os
import re

# Replace this with the directory containing your fp1 XML files
directory = "/Users/ntonthat/Downloads/fuji-x-weekly-simulation-profiles/weekly/x-trans_iv/xt4/"

# Initialize a set to store unique FilmSimulation values
unique_film_simulations = set()


# Regex pattern to match FilmSimulation values
pattern = r"<FilmSimulation>(.*?)</FilmSimulation>"

# Iterate over each file in the directory
for filename in os.listdir(directory):
    filepath = os.path.join(directory, filename)

    # Read the content of the file
    with open(filepath, encoding="utf-8") as file:
        content = file.read()

        # Find all matches of the pattern
        matches = re.findall(pattern, content)
        for match in matches:
            unique_film_simulations.add(match)
# unique_film_simulations now contains all unique FilmSimulation values
