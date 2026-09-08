# Comments on Meta ads, mechanically

## Ad comments do not live on the ad

This is the thing that stops most people before they start. A comment left on your
Facebook or Instagram ad is attached to the **page post** behind the ad's creative, not
to the ad object. For a dark post (a creative created for ads and never published to the
page timeline) that post exists and is reachable, but it does not appear on your page and
you will never find it by scrolling.

The resolution chain:

```
ad  ──►  adcreative  ──►  effective_object_story_id  ──►  "{page_id}_{post_id}"
                                                     ──►  GET /{post_id}/comments
```

`effective_object_story_id` is the field to read from the creative. It resolves to the
real post id for both published posts and dark posts, which is why it is the one to use
rather than `object_story_id`.

Two consequences that surprise people:

- **One post can back many ads.** Duplicating an ad set often reuses the same creative, so
  the same comment thread is shared across ads. Moderate the post, not the ad.
- **Instagram comments on the same creative are a separate thread**, reached through the
  Instagram media id, not the page post. Handling one and not the other leaves half the
  spam visible on the half of your delivery that is on Instagram.

## Hide, do not delete

Hiding sets `is_hidden` on the comment. The comment stays visible to its author and to
that author's friends, which is exactly how Facebook's own hide function behaves.

Deleting removes it for everyone, including the author, who then notices, and the next
comment is about censorship rather than about your product. Hiding is quieter, reversible,
and does not create a second problem.

```
POST /{comment-id}   is_hidden=true      hide
POST /{comment-id}   is_hidden=false     undo
```

Both need a page access token with the engagement management permission for the page.
Get the permission scope from the current Graph API documentation rather than from a blog
post; Meta renames these.

## Reading comments

- `GET /{post-id}/comments` with `filter=stream` returns replies as well as top-level
  comments. Spam is very often a reply on a legitimate comment, where nobody looks.
- Paginate properly. A viral post has thousands of comments and the first page is the
  oldest or the newest depending on `order`, never "the ones that matter".
- Ask for `is_hidden` in the field list and skip what is already hidden. Re-hiding a
  hidden comment is a wasted call, and on a busy account those add up against your rate
  limit.
- Store the comment id and your verdict. Re-evaluating the whole thread every minute is
  what gets an app throttled.

## Rate limits

Page-level rate limits are computed from your call volume and the page's audience size.
Two habits keep you inside them:

- **Poll on a schedule, not per event.** A minute is fast enough for spam; a second is
  not meaningfully faster and costs sixty times the quota.
- **Only fetch comments newer than the last one you saw**, using `since` and the id you
  stored, instead of re-reading the thread.

## Token handling

The page access token is the only secret in this system that can be used against you, so
treat it like one:

- Encrypt it at rest with authenticated encryption; the key lives in a secret manager, not
  beside the ciphertext.
- Send it as a `Bearer` header on reads and in the form body on writes. Never in a query
  string, where it lands in proxy logs and error reports.
- Redact it from every log line before the line is written, not after.
- A dashboard may set it and must never read it back, not even masked. A status endpoint
  returns a boolean.

## Comment text is untrusted input

A comment can contain HTML, script tags, or invisible Unicode. Render it with
`textContent`, never `innerHTML`, and never interpolate it into a shell command, a SQL
string or a prompt. If you feed comments to a model for classification, remember that a
comment is attacker-controlled text: see
[invisible-text-forensics](https://github.com/Hiberius/invisible-text-forensics) for what
can be hidden inside one.
