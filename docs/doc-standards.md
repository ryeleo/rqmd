# Documentation Standards
We write technical but user-friendly documentation.
Lots of headings to make it quick to navigate.
Split documents when they get too long into smaller helpful chunks.
Think about writing documentation as if it were a web article that you would actually want to read yourself -- this helps keep things concise, clear, and engaging enough to not fall asleep while reading it.

## No Secrets in git repos docs (or code)
There should not be any secrets in git repositories! Keep them in your own key / secret vault instead!


## Prefer Many-Smaller-Pages Over One-Large-Page 
Pages can get hard to read when they get too long. A good strategy when a page starts getting to long is to create an Index Page (discussed below), then split the document into many child pages.


## Introduce and Explain Acronyms / Jargon 
Whenever an acronym or jargon is first used in any page:

Spell out the acronym, and put the acronym in parenthesis after it
Example: "We use Authorization, Authentication and Accounting (AAA) to maintain..."
Any additional context or connotations that the reader might like to know about, put those details into an "Info" Macro.
Example: 
Authorization, Authentication and Accounting (AAA)

> **ℹ️ Info:** "The authentication, authorization, and accounting (AAA) Service Framework provides a single point of contact for all the authentication, authorization, accounting, address assignment, and dynamic request services that the router supports for network access. The framework supports authentication and authorization through external servers, such as RADIUS."
>
> from ["AAA Service Framework Overview" Juniper Networks Docs](https://www.juniper.net/documentation/en_US/junos/topics/concept/aaa-service-framework-overview.html)


## Prefer Hyperlinks over URLs

[Hyperlinks](https://en.wikipedia.org/wiki/Hyperlink) are a mechanism for embedding a URL into text. Much preferred over pasting a raw URL into documentation, because it is more readable and easier to understand the context of the link.

## Use Headings
Rules for using headings:

1. Start from h1,
2. Never skip heading levels (don't go from h1→ h3, make sure there is an h2 in the middle)

## Use Ordered/Unordered Lists
It can be very helpful to break up information into a list, when it would otherwise be a long paragraph.

- Use unordered lists when the order of items does not matter.

Sometimes, it is useful to turn long unordered lists into ordered lists. Why? It enables colleagues to more easily reference/discuss a specific item in a list.

1. This is some fact
2. This is another fact
3. This is some fact.
4. This fact comes after the prior fact.

## Use "Info", "Note", and "Warning" block quotes
These three macros should be used where they help make the document easier to read!
Do not add them in excess, but do not be afraid to use them when they can help make the document easier to read and understand.

> **Tip:** Tip Macros can be used to add a tip based on the current context of the document. They can be used to add helpful information that is not critical, but is probably useful for the reader to know.

> **ℹ️ Info:** Info Macros can be used to add extra context that you expect the audience does not need to read.

> **⚠️ Note:** Note Macros can be used to repeat and call out important information that you really want the audience to read.

> **‼️ WARNING ‼️:** Warning Macros should be used only in very important cases – this should hold critical information that you want EVERY reader to read (to avoid a resume generating event). 


## Add Page Banners

We can use the "Warning Macro" in confluence to effectively add a 'banner' to the top of any page.

To make a warning Macro appear as a 'banner' on a page: make sure to put it at the VERY top of the document, so it is the very first thing rendered (above all h1 headings).


## Page Naming Convention

For our top-level pages, do not add "Network Services" Prefix
TBD: We prefer to not embed 'namespace' information in page names, unless it makes sense (lets compare NTS Jenkins (Sunsetting) and AAA Infrastructure)
On the contrary: For deeper pages that pertain only to one single system, it definitely can make sense to prefix child pages with
Keywords that we like using in our page names:
"How-to" indicates 
"Config" indicates that this document discusses the configuration of some service/product/solution.
Example: "SolarWinds Network Discover Config"
"sunsetting" indicates that this document is for some infrastructure/service that we no longer plan on maintaining.
Once the underlying infrastructure/service is gone, the related document(s) should be deleted! (or archived)
Use Table of Contents
Add the Table of Contents at (or near) the top of pages if it might help readability. When a page doesn't fit on your screen (and contains multiple headings) it is useful to add a table of contents.


## Use Index Pages
When you have a lot of documentation, it can be helpful to create an index page that links to all the other pages. This can help readers find the information they are looking for more easily.

Optional: Add a sentence or two at the very top of the page to discuss the index page's purpose.
Keep the Index Page very brief.

