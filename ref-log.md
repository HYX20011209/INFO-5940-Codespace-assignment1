
# Reflection Log - Assignment 2

## What I Learned

Building a multi-agent workflow taught me how different AI agents can collaborate to produce higher-quality results. The Planner-Reviewer architecture mirrors real-world planning processes where one person brainstorms while another validates. I learned that separating concerns—creative planning versus critical review—leads to more robust outputs. The Planner can focus on comprehensive itinerary design without worrying about real-time accuracy, while the Reviewer handles verification.

## Challenges and Solutions

The main challenge was designing effective prompts that enabled meaningful collaboration. Initially, my Reviewer agent simply approved plans without critical analysis. I solved this by explicitly requiring a "Delta List" format, forcing the agent to identify specific issues and propose fixes. Another challenge was balancing detail with conciseness in the Planner's output. I structured the prompt to enforce consistent formatting (time blocks, costs, notes) which made the output easier for both users and the Reviewer to parse.

Getting the internet_search tool integration right took iteration. The Reviewer needed clear instructions on when to search—not for every detail, but for critical information like opening hours and current prices that change frequently.

## Design Choices

I gave each agent a clear professional identity ("Planner Agent specialized in..." vs "Reviewer Agent specializing in...") which helped establish distinct voices. The output format specifications were crucial—the Planner uses time-blocked schedules while the Reviewer follows a four-part validation structure. This creates a natural workflow where the Planner's structured output becomes easy input for systematic review.

I intentionally made the Reviewer constructive rather than purely critical, asking it to produce a "Revised Itinerary" rather than just listing problems. This ensures users always get a polished final product.

---

## External Tools and Assistance

**Tools used:**
- ChatGPT for prompt refinement advice
- Tavily API for internet search functionality
- GitHub Codespaces development environment

