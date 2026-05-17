import pickle

# load metadata only
with open("metadata.pkl", "rb") as f:
    metadata = pickle.load(f)


def search_assessments(query, top_k=10):
    query = query.lower()

    scored_results = []

    for item in metadata:
        text = (
            item.get("name", "")
            + " "
            + item.get("description", "")
            + " "
            + item.get("test_type", "")
        ).lower()

        score = 0

        for word in query.split():
            if word in text:
                score += 1

        if score > 0:
            scored_results.append((score, item))

    scored_results.sort(key=lambda x: x[0], reverse=True)

    return [item[1] for item in scored_results[:top_k]]


if __name__ == "__main__":
    query = input("Enter hiring query: ")

    results = search_assessments(query)

    print("\nTop recommendations:\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. {result['name']}")
        print(f"URL: {result['url']}")
        print(f"Description: {result.get('description', 'N/A')}")
        print("-" * 50)
