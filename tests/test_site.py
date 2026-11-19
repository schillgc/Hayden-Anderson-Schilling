"from html.parser import HTMLParser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DocumentContractParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.links = []
        self.headings = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.tags.append((tag, attributes))
        if tag == "a":
            self.links.append(attributes)
        if tag == "h1":
            self.headings.append(tag)


class StaticSiteContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "styles.css").read_text(encoding="utf-8")
        cls.parser = DocumentContractParser()
        cls.parser.feed(cls.html)

    def test_document_has_language_and_semantic_landmarks(self):
        html_tags = [attrs for tag, attrs in self.parser.tags if tag == "html"]
        main_tags = [attrs for tag, attrs in self.parser.tags if tag == "main"]
        nav_tags = [attrs for tag, attrs in self.parser.tags if tag == "nav"]

        self.assertEqual(len(html_tags), 1)
        self.assertEqual(html_tags[0].get("lang"), "en")
        self.assertEqual(len(main_tags), 1)
        self.assertEqual(len(self.parser.headings), 1)
        self.assertEqual(len(nav_tags), 1)
        self.assertTrue(nav_tags[0].get("aria-label"))

    def test_all_external_links_use_safe_new_tab_attributes(self):
        self.assertGreater(len(self.parser.links), 0)
        for link in self.parser.links:
            with self.subTest(href=link.get("href")):
                href = link.get("href", "")
                self.assertTrue(href.startswith("https://"), href)
                self.assertEqual(link.get("target"), "_blank")
                rel = set(link.get("rel", "").lower().split())
                self.assertIn("noopener", rel)
                self.assertIn("noreferrer", rel)

    def test_decorative_resource_icons_are_hidden_from_screen_readers(self):
        icons = [
            attrs for tag, attrs in self.parser.tags
            if tag == "span" and "resource-icon" in attrs.get("class", "").split()
        ]
        self.assertEqual(len(icons), len(self.parser.links))
        self.assertTrue(all(icon.get("aria-hidden") == "true" for icon in icons))

    def test_local_stylesheet_and_dependency_free_page_are_preserved(self):
        self.assertIn('href="styles.css"', self.html)
        self.assertNotRegex(self.html, r"(?i)<script[^>]+src=")
        self.assertNotIn("http://", self.html)

    def test_keyboard_focus_and_reduced_motion_preferences_are_supported(self):
        self.assertIn(".resource-card:focus-visible", self.css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.css)

    def test_layout_remains_responsive_without_a_fixed_card_count(self):
        self.assertRegex(self.css, r"grid-template-columns:\s*repeat\(auto-fit")
        self.assertRegex(self.css, r"min-width:\s*320px")


if __name__ == "__main__":
    unittest.main()
