from src.tools.tools import web_search, scrape_url

result = web_search.invoke("What is the latest news about AI research?")
results = scrape_url.invoke("https://en.wikipedia.org/wiki/Paris")

print(result)
print(results)