"""Technology detection tests."""

from ab_hub.analyzers.technology import detect_from_file_tree, detect_from_languages


def test_languages():
    langs = {"Python": 12000, "JavaScript": 3000}
    result = detect_from_languages(langs)
    names = {t.name for t in result}
    assert "Python" in names
    assert "JavaScript" in names


def test_file_signatures():
    paths = ["package.json", "src/index.ts", "Dockerfile", "requirements.txt"]
    result = detect_from_file_tree(paths)
    names = {t.name for t in result}
    assert "Node.js" in names
    assert "Docker" in names
    assert "Python" in names
