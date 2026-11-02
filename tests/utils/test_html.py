"""Tests for cleaning HTML in resource descriptions."""

import pytest

from app.transform.utils.html import clean_html


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        pytest.param(
            "A normal resource description.",
            "A normal resource description.",
            id="normal-description",
        ),
        pytest.param(
            '  <p>A <strong>useful</strong> <a href="https://example.com">resource</a>.</p>  ',
            "A useful resource.",
            id="html-tags",
        ),
        pytest.param(
            "&lt;p&gt;Research&nbsp;&amp;&nbsp;training &#8212; &#x3B1;&lt;/p&gt;",
            "Research & training — α",
            id="html-encoded-as-entities",
        ),
        pytest.param(
            "<div><p>A <strong><em>useful</em></strong> resource.</p></div>",
            "A useful resource.",
            id="nested-tags",
        ),
        pytest.param(
            "&amp;lt;p&amp;gt;Research&amp;amp;nbsp;&amp;amp;amp; training&amp;lt;/p&amp;gt;",
            "Research & training",
            id="nested-entities",
        ),
    ],
)
def test_clean_html(description, expected):
    assert clean_html(description) == expected


def test_clean_html_list():
    descriptions = [
        "A normal description.",
        "<p>An <strong>HTML</strong> description.</p>",
        "&lt;p&gt;An encoded description.&lt;/p&gt;",
        "&amp;lt;p&amp;gt;A nested description.&amp;lt;/p&amp;gt;",
        None,
        "",
    ]

    assert clean_html(descriptions) == [
        "A normal description.",
        "An HTML description.",
        "An encoded description.",
        "A nested description.",
        None,
        "",
    ]


@pytest.mark.parametrize("description", [None, "", []])
def test_clean_html_preserves_empty_values(description):
    assert clean_html(description) == description
