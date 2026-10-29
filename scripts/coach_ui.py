"""Compose the training desk from small, editable UI assets."""
from pathlib import Path
import base64

ROOT = Path(__file__).resolve().parents[1]


def enhance(html):
    assets = ROOT / 'assets'
    picture = base64.b64encode((ROOT / 'references/Background.jpg').read_bytes()).decode()
    logo = 'data:image/png;base64,' + base64.b64encode((assets / 'brand-logo.png').read_bytes()).decode()
    html = html.replace('__LOGO__', logo)
    css = (assets / 'dashboard.css').read_text().replace('__HERO__', 'data:image/jpeg;base64,'+picture)
    a = html.index('<style>') + len('<style>')
    b = html.index('</style>', a)
    html = html[:a] + css + html[b:]
    a = html.index('<header>')
    b = html.index('</header>', a)+len('</header>')
    html = html[:a]+(assets/'desk.html').read_text().replace('__LOGO__', logo)+html[b:]
    history_start = html.index('<div id="syncNotice"')
    html = html[:history_start] + '<details class="workspace-drawer history-drawer" id="history"><summary><span><small>06</small> History</span><span class="drawer-action">Your progress <b>+</b></span></summary><div class="history-heading"><div><div class="kicker">THE BIGGER PICTURE</div><h2>Activities<span>.</span></h2><div id="coverage" class="note"></div></div></div>' + html[history_start:]
    html = html.replace('</main>','</details><footer class="desk-footer"><span>THE DAILY PRACTICE</span><span>Built for the long run.</span><a href="#top">Back to top ↑</a></footer></main>',1)
    return html.replace('</body>','<script>'+(assets/'coach.js').read_text()+'</script></body>')
