import asyncio
import cognee

async def main():
    # 1. Clean up any corrupted local cache data from previous failed attempts
    await cognee.prune.prune_data()
    await cognee.prune.prune_system()
    
    # 2. Add your text
    print("Ingesting text into local Cognee knowledge engine...")
    await cognee.add("Natural language processing (NLP) is an interdisciplinary subfield of computer science.")
    
    # 3. Make Cognee process the text using Llama 3.1 & Nomic Embeddings
    print("Cognifying and creating the knowledge graph...")
    await cognee.cognify()
    print("Success!")

if __name__ == "__main__":
    asyncio.run(main())