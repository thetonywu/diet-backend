# Knowledge Base Research Prompt

Use this prompt to research a single KB item and add it as a new file to the knowledge base.

---

## Instructions

You are a researcher building a knowledge base for an animal-based diet chatbot. Your job is to pick one unchecked item from the todo lists, do deep research on it, write it up, and save it as a new markdown file.

### Step 1: Pick an Item

Open `knowledge-base/top-questions.md` and `knowledge-base/top-goals.md`. Find an unchecked item (`- [ ]`) that does not already have a corresponding file in `knowledge-base/articles/`. Pick one and note its exact text.

### Step 2: Research

Do deep research on the topic using Paul Saladino's content as the primary source. Use these sources in priority order:

1. **Paul Saladino's YouTube videos** — search his channel (youtube.com/@PaulSaladinoMD) for videos on the topic. Watch or read transcripts of the most relevant ones. Note his specific claims, recommendations, and reasoning.
2. **Paul Saladino's podcast** (Fundamental Health) — search for relevant episodes and extract key points.
3. **Heart & Soil website** (heartandsoil.co) — check for blog posts, guides, or product pages related to the topic.
4. **Paul Saladino's website** (paulsaladinomd.com) — check for articles or guides.
5. **Supporting sources** — look for studies, papers, or other experts Paul cites to back up his positions. Include these as references.

For each source you use, note:
- The title of the video/episode/article
- The URL
- The key claims or recommendations made

### Step 3: Write the Article

Create a new markdown file in `knowledge-base/articles/` using this format:

```
knowledge-base/articles/<slug>.md
```

Where `<slug>` is a short kebab-case name for the topic (e.g., `seed-oils`, `boost-testosterone`, `animal-based-vs-carnivore`).

Use this template for the article:

```markdown
# <Title as a Clear Question or Goal Statement>

## TLDR

<2-3 sentence summary a chatbot could use as a quick answer>

## Background

<Why this question/goal matters to people on or considering the animal-based diet. 2-3 sentences.>

## What Paul Saladino Recommends

<His specific position, recommendations, and reasoning. Be concrete — include specific foods, amounts, protocols, or brand names when he provides them. Use bullet points for actionable items.>

## Key Points

<Bullet list of the most important facts and claims, written as standalone statements the chatbot could reference>

- Point 1
- Point 2
- Point 3
- ...

## Common Mistakes

<What people get wrong about this topic, or pitfalls to avoid. Bullet list.>

## Sources

<List of sources used, with URLs when available>

- [Video/Article Title](url) — brief note on what it covers
- ...
```

Guidelines for writing:
- Write in a neutral, informative tone. Present Paul Saladino's views as his recommendations, not as universal facts.
- Be specific and actionable. "Eat liver" is better than "eat organ meats." "Cook with tallow or ghee" is better than "use healthy fats."
- Include brand names, quantities, and protocols when Paul provides them.
- Keep the article focused on the single topic. Don't try to cover everything.
- Aim for 300-800 words in the body (excluding sources).

### Step 4: Check It Off

After saving the article, update the corresponding todo list file (`top-questions.md` or `top-goals.md`) by changing the item from `- [ ]` to `- [x]`.

### Step 5: Commit

Commit both files (the new article and the updated checklist) together with a message like:

```
Add KB article: <topic title>
```

---

## File Structure

```
knowledge-base/
  top-questions.md          # Checklist of questions to research
  top-goals.md              # Checklist of goals to research
  categories.md             # Content category reference
  RESEARCH_PROMPT.md        # This file
  articles/                 # Completed research articles
    seed-oils.md
    animal-based-vs-carnivore.md
    boost-testosterone.md
    ...
```

## Quality Checklist

Before committing, verify:

- [ ] Article has all template sections filled out (TLDR, Background, Recommendations, Key Points, Common Mistakes, Sources)
- [ ] At least 2 sources are cited with URLs
- [ ] At least one source is directly from Paul Saladino's content
- [ ] Key Points are specific enough for a chatbot to use as standalone answers
- [ ] TLDR is concise enough to serve as a quick chatbot reply (2-3 sentences max)
- [ ] The corresponding checklist item is marked done
