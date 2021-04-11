# Personal blog builder

**Why** do i program a custom builder along with a number of mature ones and **Jekyll** as a default?

Well, I've spent too much time reading documentation and trying to adapt a blog builder to my minimalistic needs. Then i figured out it is much faster and clearer to generate a static blog site step by step on my own just using **Github Pages** as a free hosting service. Only basic knowledge of followed technologies is necessary to build a ready to deploy folder: **html, css, markdown**. Armed myself with **python** i got all the potency and flexibility it provides to generate things how and what i need only. 

As a result, things i do are writing articles text, and coding new small features on demand. No more hassle with asking myself what is going on under the hood of Gihub Jekyll-der and testing the site by commit-push-deploy approach, i see all the results locally.

## Repo structure

`/build` - folder with the html templates and py files contain custom logic of building static files based on source markdown files i don't track by GIT.

`/docs` - folder which Github Pages deploy on my blog Github subdomain automatically on each commit.

## Features

- Generating an article html from markdown text and media files using `commonmark` and `jinja2`.
- Generating a blog index page.
- Generating **TOC**(table of content) from the article html.
- Adding and linking source media files are contained in the article html to the repository ones.
- Comments [utteranc.es](https://utteranc.es/) attached to the articles.
- **Diff Page** shows a difference between an initial content of an article and the latest one.

