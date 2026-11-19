# Piper's Library

A static page listing the children's books we already own, so family can check before buying.

## Adding a book

The easy way: paste a link or an ISBN into the helper script.

```sh
python3 tools/add_book.py "https://www.amazon.com/Corduroy-Don-Freeman/dp/0140501738"
python3 tools/add_book.py 9780140501735 --notes "board book"
python3 tools/add_book.py "<bookshop.org / B&N / Goodreads link>" --series "Elephant & Piggie"
```

It finds the ISBN, looks up the title and author (Open Library, then Google Books),
saves the cover to `covers/`, and adds the book to `books.js`. Only Python 3 is needed.
Amazon Kindle links have no ISBN; use the hardcover/paperback page instead.
If a lookup comes up empty, pass `--title` and `--author` yourself.

Then commit `books.js` and the new file in `covers/`, and push.

### By hand

Edit `books.js` and add a line inside the list:

```js
{ title: "Corduroy", author: "Don Freeman", isbn: "9780140501735" },
```

`isbn` is optional; when present, the cover comes from Open Library. `series` and `notes` are optional too.

## Previewing locally

Open `index.html` in a browser. No build step or server needed.

## Publishing on GitHub Pages

1. Push this repo to GitHub.
2. In the repo, go to **Settings → Pages**.
3. Under **Build and deployment**, pick **Deploy from a branch**, branch `main`, folder `/ (root)`.
4. The site appears at `https://<username>.github.io/<repo-name>/` within a minute or two.

Every push to `main` updates the site.
