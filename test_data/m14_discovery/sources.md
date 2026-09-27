# Free-book sources for M14 scale testing

Web research: Project Gutenberg offers free ebooks and documents automated bulk access at https://www.gutenberg.org/policy/robot_access.html and https://www.gutenberg.org/help/mirroring.html . Its terms direct bulk downloads to mirrors: https://www.gutenberg.org/policy/terms_of_use.html . Do not crawl individual book pages for this fixture.

Owner selected a mixed fixture. Reuse the existing 100 Project Gutenberg samples acquired via the documented ibiblio rsync mirror on 2026-09-20. Their source pages, rights statements and original file hashes are recorded in ../free_ebooks_100/manifest.json (relative to test_data). Creation checks every reused format against that manifest. Original license notices remain embedded. No new ebook download is needed. Catalog rights statements are US public-domain statements, not a worldwide copyright certification.

Remaining 9,900 books contain original generated test paragraphs, not scraped or copied modern publications. They are explicitly labeled fixture content. The collection measures catalog scale, not the content diversity or disk footprint of 10,000 distinct full-length publications.

Calibre fixture creation uses its documented add_books and set_cover interfaces: https://manual.calibre-ebook.com/db_api.html . Installed runtime is pinned to 9.2.1; current online documentation can describe newer versions, so actual API execution is verified in that runtime.
