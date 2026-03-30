## User Story based??

Hmm... we should add support/documentation for changing "Requirment Domains" to "User Stories" I think. And mayb


## AI Workflow

Update AI to have two primary worker skills:

### Brainstorm

1. User does planning in brainstorm.md
2. Then creates requirements from their brainstorm.md with hepl from AI agent.

### Implement

1. AI agent, making sure to update requirements and tests as they go.
2. After implementing a feature make sure:
    1. The tool itself runs
    2. All tests pass
    3. Changlog is updated
    4. Requirements are updated (using `rqmd --update...` or directly editing the markdown files)


## Performance Improvements

MAybe use Rust to reimplement this whole solution.

Maybe use Rust where possible to speedup this code (I know that's why `uv` is so fast, for example). Maybe we can have a Rust core for parsing and JSON contract generation, and then a thin Python wrapper for the CLI and interactive features? This would be a big undertaking but could make the tool much more performant, especially for large requirement sets.

##


RQMD-CORE-013 (domain/index sync maintenance) since it would reduce manual doc drift over time.

## Priority for domain and sub-domain

Unsure if it makes sense, but might be nice to add priority to domains and subdomains... right?

## Option to add Agent and Skill instructions for AI Agents

Rqmd should offer to install a core set of agent and skill instructions for AI agents to use when working with the tool. This would include instructions for how to interpret the JSON contract, how to use the `rqmd` CLI in various modes, and how to update requirements and documentation as part of implementation work. This would help ensure that AI agents can effectively contribute to the project without needing extensive manual guidance on how to interact with the tool and maintain alignment between code, tests, requirements, and documentation.

## Filter support at CLI

- should be able to combine filters.
- OR between different filter flags, AND within the same flag.

- Should be able to filter on anything:
    - "--has-link" (and the inverse, "--no-link")
    - "--has-flag" (and the inverse, "--no-flag")
    - "--priority"



## External Links

Core-engine: Add a "Links" section to each Requirement, so that ppl can add links to their requirements. This way, external systems (e.g. github issues, TDX, Jira) can easily be linked to requirements, and users can quickly jump to related work in other systems from these requirement docs (if gh-cli is enabled, the AI agent could even make updates directly to linked GH issues, just saying).

Core-engine: Make links as a top-level field, so it is very easy.

UX: Let the user enter url or markdown hyperlink -- if they skip the markdown formatting and just use url, offer to optionally take 'label: ' next and automatically turn it into a hyperlink!



## Schema Versioning

The schema for rqmd **is** version of this rqmd pakcckag. The rqdmmdersion should be part of the json contract and shnoudl be in requirements/README.md.


## Debug why rqmd fails for Speed Shooting VR

- ValueError: Unrecognized status value: 💻 Desktop-Verified

## TODO

follow-on requirement for --update-flagged ID=true|false so automation can mutate flagged state directly too.

## codify the "implement all proposed items" approach in the README and contribution guidelines

This works great with AI agents!

```
Continue! Try to implement all 48 proposed RQMDs this time if you can! Make sure to check your priorities after every 3-5 or so depending on how complicated the work is and how interdependent they might be.

Do the easier ones first so we see how far you get before running into something you cannot do.

I've set `chat.agent.maxRequests=1500` so you can go for a while!

Make sure to check that `rqmd` runs for you, and there aren't regressions in our test suite as you go! And update the test suite as you go! And update requirements as you go using `rqmd --update...`! And update requirements directly if they change as you go!
```


continue updating reqs!
Then continue implementing features with tests and making sure you keep requirements well docuemnted as you go as details reveal themselves!


## Screen Write vs Scroll?

Consider if we should change the UI to be screen write instead of scrolling style. That would make the UI much more snappy, and capable of handling page changes more gracefully, which we do a lot of in this CLI tool.

## Full Blocking Implementation

Upgrdaing "block reason" to provide the user an option of which other requirement it is blocked by. This will be optional, but a quick way to insert a MD hyperlink to another REQ.
Implementaiotn wise, hold an index at runtime of all issues 'search tokens', so that the user can easily quickly type in any word from the title the title or id REQ to find it easily then select it.
Consider making this app no longer a scrolling app but a fixed terminal 
Add to the schema for requirements/.md docs to include this field as an optional field. Then add the ability to edit it in interactive mode when setting status to blocked, and also to edit or remove it when changing status from blocked to something else.




## ctrl + z

Add a path to capture "^Z" and treat it as an undo for the whole app!

ctrl+y or ctrl+shift+z for redo!

This becons the idea of saving a state change log, so that undo/redo persists after a crash too...


## README.md should be fully generated

This file should be a true index of the last time the tool ran.
Maybe even we should "assume that all updates to the markdown files are made via the tool."

## ReqMD instead of rqmd?

I think ReqMD is nicer really tbh. This can be done at some point before first release, or after I guess if no one is name squatting `reqmd` on pypi.org.

## Rename Key feature?

Finally, Probably should also have a feature for easily changing the key for all files for quickly renaming from the default of "REQ-" to something more project specific. Add a new requirement, but don't 

