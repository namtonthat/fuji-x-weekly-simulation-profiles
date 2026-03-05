import pytest
from bs4 import BeautifulSoup


@pytest.fixture
def sample_html():
    # Note: Ensure the outer container wraps all the top-level <strong> tags.
    return """
    <div>
        <strong>Film Simulation: Eterna Bleach Bypass</strong><br/>
        <strong>Dynamic Range: DR400</strong><br/>
        <strong>Grain Effect: Strong, Large</strong><br/>
        <strong>Color Chrome Effect: Strong</strong><br/>
        <strong>Color Chrome FX Blue: Off (X-Trans V); Weak (X-Trans IV)</strong><br/>
        <strong>
            White Balance: <strong>Fluorescent 1</strong>, -2 Red &amp; -4 Blue
        </strong><br/>
        <strong>Highlight: -2</strong><br/>
        <strong>Shadow: -1</strong><br/>
        <strong>Color: +2</strong><br/>
        <strong>Sharpness: -1</strong><br/>
        <strong>Fluorescent 1</strong><br/>
        <strong>High ISO NR: -4</strong><br/>
        <strong>Clarity: -2</strong><br/>
        <strong>ISO: Auto, up to ISO 6400</strong><br/>
        <strong>Exposure Compensation: +1/3 to +1 (typically)</strong><br/>
        <strong>Fujifilm X-T5</strong><br/>
        <strong>Amazon</strong><br/>
        <strong>B&amp;H</strong><br/>
        <strong>Moment</strong><br/>
        <strong>Wex</strong><br/>
        <strong>Nuzira</strong><br/>
        <strong>Fujifilm X-T5</strong><br/>
        <strong>Amazon</strong><br/>
        <strong>,</strong><br/>
        <strong>B&amp;H</strong><br/>
        <strong>Moment</strong><br/>
        <strong>Wex</strong><br/>
        <strong>Nuzira</strong>
    </div>
    """


@pytest.fixture
def strong_tags(sample_html):
    soup = BeautifulSoup(sample_html, "html.parser")
    # Only select top-level <strong> tags that are direct children of the <div>
    return soup.select("div > strong")
