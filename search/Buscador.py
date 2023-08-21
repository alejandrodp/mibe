import json

# Load source (JSON) data and return it as a Python dictionary
def load_data_from_json(file_name):
    with open(file_name, 'r') as file:
        data = json.load(file)
    return data

# Recursive function that performs the search based on the given search term or filter
def search_by_filters(node, search_term, exclusion_set, results):
    # Check if the search term is present in the 'name' or 'description' fields (case-insensitive)
    if search_term in node['name'].lower() or search_term in node.get('description', '').lower() or search_term in node.get('nodetype', '').lower():
        # Remove excluded keys (columns) before appending to results
        filtered_node = {k: v for k, v in node.items() if k not in exclusion_set}
        results.append(node)

    # Recursively search in the children nodes
    for child in node.get('children', []):
        search_by_filters(child, search_term, exclusion_set, results)

def display_results(data, search_term):
    search_results = []
    exclusion_set = {'children', 'object type', 'class'}
    search_by_filters(data["tree"], search_term, exclusion_set, search_results)

    return search_results

#Main program, takes input from user and displays the result
def main():
    json_file = '/home/alejandro/projects/levelup/parsed/ARUBAWIRED-FAN-MIB_tree.json'
    data = load_data_from_json(json_file)

    while True:
        search_term = input("Enter the filter to search (or 'exit' to quit): ").lower()
        if search_term == 'exit':
            break

        results = display_results(data, search_term)
        if not results:
            print("No results found.")
        else:
            print(*results, sep="\n\n")

if __name__ == "__main__":
    main()

