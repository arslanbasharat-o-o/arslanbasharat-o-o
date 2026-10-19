# Maintaining this profile

The README features public projects and original terminal-style SVG artwork.
Both artwork panels have light, dark, desktop, and mobile versions. Terminal
cursors and an accent sweep loop continuously; the monogram gently pulses.
Text and calendar cells remain visible from the first frame. Animations respect
reduced-motion preferences, which show a static profile instead.
Introduction and project information is also available as text or image alt text.

## Daily contribution refresh

The `Refresh profile activity` workflow runs daily at 06:17 UTC (11:17 AM
Pakistan time), and can be run manually from the Actions tab. GitHub may delay
scheduled runs. It reads the unauthenticated contribution HTML shown on the
public profile. It needs no personal access token, external stats service,
Python packages, or private repository access.

The built-in repository token is used only to commit generated files. Yearly
totals follow GitHub's public headline; daily counts follow its public calendar.
GitHub can briefly cache those separately, so `total` and `daily_total` can differ.
Anonymous private contribution counts are included only as GitHub already shows
them publicly. No private project names or repository details are fetched.
The mobile grid shows 16 weeks; summary statistics cover the full fetched year.
The longest streak counts consecutive calendar days with contributions in that window.

The parser rejects incomplete calendars, unknown count formats, gaps, and stale
responses. Fetch failures leave the last committed artwork intact and visibly
fail the workflow rather than replacing it with invented stats.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/update_profile.py
```

## Editing

- Change colors, introduction, or layout in `scripts/update_profile.py`.
- Change projects and contact links in `README.md`.
- Regenerate and commit SVGs with source changes.
- Keep project links pointed at public repositories.

Inspired by [Avi Vashishta's animated profile guide](https://www.avivashishta.com/blog/build-animated-github-profile-readme).
The artwork, layout, and generator are original implementations.
