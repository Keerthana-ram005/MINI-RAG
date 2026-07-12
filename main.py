from router import route_query

def main():
    print("=== Mini Agentic RAG ===")

    while True:
        query = input("\nYou: ")

        if query.lower() in ["exit", "quit"]:
            break

        answer = route_query(query)

        print("\nAssistant:", answer)


if __name__ == "__main__":
    main()