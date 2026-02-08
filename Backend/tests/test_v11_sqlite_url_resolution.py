import unittest

from app.db_url import PROJECT_ROOT, normalize_sqlite_url


class V11SqliteUrlResolutionTest(unittest.TestCase):
    def test_relative_sqlite_url_is_normalized_to_project_root(self):
        normalized = normalize_sqlite_url("sqlite+pysqlite:///./local_dev.db")
        expected = f"sqlite+pysqlite:///{(PROJECT_ROOT / 'local_dev.db').resolve()}"
        self.assertEqual(normalized, expected)

    def test_non_relative_sqlite_url_is_unchanged(self):
        original = "sqlite+pysqlite:////tmp/example.db"
        self.assertEqual(normalize_sqlite_url(original), original)


if __name__ == "__main__":
    unittest.main()
