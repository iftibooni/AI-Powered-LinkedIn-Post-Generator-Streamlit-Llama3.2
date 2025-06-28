import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from LLM import llm

def process_posts(raw_file_path, processed_file_path="data/processed_posts.json"):
    enriched_posts = []
    with open(raw_file_path, encoding='utf-8') as file:
        posts = json.load(file)

    for post in posts:
        metadata = extract_metadata(post['text'])
        post_with_metadata = post | metadata
        enriched_posts.append(post_with_metadata)

    for epost in enriched_posts:

        print(epost)

    unified_tags=get_unified_tags(enriched_posts)

    for post in enriched_posts:
        current_tags=post['tags']
        new_tags={unified_tags[tag] for tag in current_tags}
        post['tags']=list(new_tags)

    with open(processed_file_path, encoding='utf-8', mode="w") as outfile:
        json.dump(enriched_posts, outfile, indent=4)


def get_unified_tags(posts_with_metadata):
    unique_tags = set()
    for post in posts_with_metadata:
        unique_tags.update(post['tags'])

    escaped_tags = [tag.replace('{', '{{').replace('}', '}}') for tag in unique_tags]
    unique_tags_list = ', '.join(escaped_tags)

    template = '''I will give you a list of tags. You need to unify tags with the following requirements:
    1. Tags are unified and merged to create a shorter list.
        Example 1: "Jobseekers", "Job Hunting" → "Job Search"
        Example 2: "Motivation", "Inspiration", "Drive" → "Motivation"
        Example 3: "Personal Growth", "Personal Development" → "Self Improvement"
        Example 4: "Scam Alert", "Job Scam" → "Scams"
    2. Each tag should follow title case convention (e.g., "Job Search")
    3. Output should be a JSON object with mapping of original to unified tags
        Example: {{"Jobseekers": "Job Search", "Job Hunting": "Job Search"}}

    Here is the list of tags:
    {input_tags}''' # Changed {tags} to {input_tags}

    pt = PromptTemplate.from_template(template)
    chain = pt | llm
    response = chain.invoke(input={"input_tags": unique_tags_list}) # Changed "tags" to "input_tags"

    try:
        json_parser = JsonOutputParser()
        res = json_parser.parse(response.content)
    except OutputParserException:
        raise OutputParserException("Failed to parse unified tags")
    return res


def extract_metadata(post):
    """Extracts metadata from a LinkedIn post including line count, language, and tags."""
    template = """
    You are given a LinkedIn post. You need to extract:
    1. Number of lines
    2. Language of the post (English or Urdu+English)
    3. Up to two text tags

    Return a JSON object with exactly these keys:
    - line_count (number)
    - language ("English" or "Urdu+English")
    - tags (array of max 2 strings)

    Post content:
    {post}
    """

    pt = PromptTemplate.from_template(template)
    chain = pt | llm
    response = chain.invoke(input={'post': post})

    try:
        json_parser = JsonOutputParser()
        res = json_parser.parse(response.content)
        return res
    except OutputParserException:
        raise OutputParserException("Context too big. Unable to parse post metadata.")
    return res

if __name__ == "__main__":
    process_posts("data/raw_posts.json","data/processed_posts.json")